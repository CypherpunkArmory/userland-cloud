import os
from typing import Tuple, cast

import nomad
from dpath.util import values

from app import db
from app.models import Subdomain, Tunnel, User
from app.services.subdomain import SubdomainCreationService
from app.utils.errors import (
    AccessDenied,
    TunnelError,
    SubdomainInUse,
    TunnelLimitReached,
)
from app.utils.json import dig

from app.utils.dns import discover_service

tunnel_limits = {"free": 1, "paid": 2}


class TunnelCreationService:
    def __init__(
        self, current_user: User, subdomain_id: int, port_type: list, ssh_key: str
    ):

        self.subdomain = None

        if subdomain_id:
            self.subdomain = Subdomain.query.get(subdomain_id)

        self.port_type = port_type
        self.ssh_key = ssh_key
        self.current_user = current_user
        # We need to do this each time so each if a nomad service goes down it doesnt affect web api
        if os.getenv("FLASK_ENV") == "production":
            self.nomad_client = nomad.Nomad(discover_service("nomad").url)
        else:
            self.nomad_client = nomad.Nomad(host=os.getenv("SEA_HOST", "0.0.0.0"))

    def create(self) -> Tunnel:
        self.check_subdomain_permissions()
        if self.over_tunnel_limit():
            raise TunnelLimitReached("")
        job_id, ssh_port, ip_address = self.create_tunnel_nomad()

        self.subdomain.in_use = True

        tunnel = Tunnel(
            subdomain_id=self.subdomain.id,
            port=self.port_type,
            job_id=job_id,
            ssh_port=ssh_port,
            ip_address=ip_address,
        )

        tunnel.subdomain = self.subdomain

        db.session.add(tunnel)
        db.session.add(self.subdomain)
        db.session.flush()

        return tunnel

    def check_subdomain_permissions(self) -> None:
        if self.subdomain and self.subdomain.user != self.current_user:
            raise AccessDenied("You do not own this subdomain")
        elif self.subdomain and self.subdomain.in_use:
            raise SubdomainInUse("Subdomain is in use")
        elif self.subdomain and self.subdomain.user == self.current_user:
            pass
        else:
            self.subdomain = SubdomainCreationService(
                self.current_user
            ).get_unused_subdomain()

    def over_tunnel_limit(self) -> bool:
        num_tunnels = self.current_user.tunnels.count()
        if num_tunnels >= tunnel_limits[self.current_user.tier]:
            return True
        return False

    def create_tunnel_nomad(self) -> Tuple[str, str]:
        """Create a tunnel by scheduling an SSH container into the Nomad cluster"""

        meta = {
            "ssh_key": self.ssh_key,
            "box_name": self.subdomain.name,
            "base_url": os.getenv("BASE_SERVICE_URL", ".local"),
        }

        result = self.nomad_client.job.dispatch_job("ssh-client", meta=meta)
        job_id = cast(str, result["DispatchedJobID"])

        # FIXME: nasty blocking loops should be asynced or something
        # Add error handling to this
        status = None
        trys = 0
        while status != "running":
            trys += 1
            status = self.nomad_client.job[result["DispatchedJobID"]]["Status"]
            if trys > 1000:
                raise TunnelError(detail="The tunnel failed to start.")

        job_info = self.nomad_client.job.get_allocations(job_id)

        allocation_info = self.nomad_client.allocation.get_allocation(
            dig(job_info, "0/ID")
        )

        allocation_node = values(allocation_info, "NodeID")
        nodes = self.nomad_client.nodes.get_nodes()

        ip_address = next(x["Address"] for x in nodes if x["ID"] in allocation_node)
        allocated_ports = values(allocation_info, "Resources/Networks/0/DynamicPorts/*")
        ssh_port = next(x for x in allocated_ports if x["Label"] == "ssh")["Value"]

        return (job_id, ssh_port, ip_address)


class TunnelDeletionService:
    def __init__(self, current_user: User, tunnel: Tunnel):
        self.current_user = current_user
        self.tunnel = tunnel
        self.subdomain = tunnel.subdomain
        if os.getenv("FLASK_ENV") == "production":
            self.nomad_client = nomad.Nomad(discover_service("nomad").url)
        else:
            self.nomad_client = nomad.Nomad(host=os.getenv("SEA_HOST", "0.0.0.0"))

    def delete(self):
        self.del_tunnel_nomad()

        if self.subdomain.reserved:
            self.subdomain.in_use = False
            db.session.add(self.subdomain)
            db.session.delete(self.tunnel)
            db.session.flush()
        else:
            db.session.delete(self.tunnel)
            db.session.delete(self.subdomain)
            db.session.flush()

    def del_tunnel_nomad(self):
        self.nomad_client.job.deregister_job(self.tunnel.job_id)
