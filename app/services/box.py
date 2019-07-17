from typing import Tuple, cast

import nomad
from dpath.util import values
from datetime import timedelta, datetime

from app import db
from app.jobs.nomad_cleanup import cleanup_old_nomad_box
from app.models import Config, Box, User
from app.services.config import ConfigCreationService
from app.jobs.nomad_cleanup import expire_running_box
from app.utils.errors import AccessDenied, BoxError, ConfigInUse, BoxLimitReached
from app.utils.json import dig

from app.utils.dns import discover_service

from typing import Optional

from flask import current_app, render_template


class BoxCreationService:
    def __init__(
        self,
        current_user: User,
        config_id: Optional[int],
        ssh_key: str,
        session_length: int = 30,  # minutes
    ):

        self.ssh_key = ssh_key
        self.current_user = current_user
        self.session_end_time = datetime.utcnow() + timedelta(minutes=session_length)
        self.session_length = session_length

        if config_id:
            self.config = Config.query.get(config_id)
        else:
            self.config = ConfigCreationService(self.current_user).create()

        # We need to do this each time so each if a nomad service goes down
        # it doesnt affect web api
        self.nomad_client = nomad.Nomad(discover_service("nomad").ip)

    def create(self) -> Box:
        self.check_config_permissions()
        job_id = None
        if self.over_box_limit():
            raise BoxLimitReached("Maximum number of opened boxes reached")
        try:
            job_id = self.create_box_nomad()
            ssh_port, ip_address = self.get_box_details(job_id)
        except BoxError:
            # if nomad fails to even start the job then there will be no job_id
            if job_id:
                cleanup_old_nomad_box.queue(job_id, timeout=60000)
            raise BoxError("Failed to create box")
        except nomad.api.exceptions.BaseNomadException:
            raise BoxError("Failed to create box")

        box = Box(
            config_id=self.config.id,
            job_id=job_id,
            ssh_port=ssh_port,
            ip_address=ip_address,
            session_end_time=self.session_end_time,
        )

        box.config = self.config

        db.session.add(box)
        db.session.add(self.config)
        db.session.flush()

        expire_running_box.schedule(
            timedelta(minutes=self.session_length), self.current_user, box, timeout=30
        )

        return box

    def check_config_permissions(self) -> None:
        if self.config.user != self.current_user:
            raise AccessDenied("You do not own this config")

    def over_box_limit(self) -> bool:
        num_boxes = self.current_user.boxes.count()
        if num_boxes >= self.current_user.limits().box_count:
            return True
        return False

    def create_box_nomad(self) -> str:
        """Create a box by scheduling an SSH container into the Nomad cluster"""

        stripped_ssh_key = "".join(i for i in self.ssh_key if 31 < ord(i) < 127)
        box_name = "box-" + (
            self.config.name if self.config.name else str(self.config.id)
        )
        new_job = render_template(
            "box.j2.json",
            ssh_key=stripped_ssh_key,
            box_name=box_name,
            bandwidth=str(self.current_user.limits().bandwidth),
            time_limit=self.session_length,
        )
        self.nomad_client.jobs.request(
            data=new_job, method="post", headers={"Content-Type": "application/json"}
        )
        return "box-client-" + box_name

    def get_box_details(self, job_id: str) -> Tuple[str, str]:
        """Get details of ssh container"""
        # FIXME: nasty blocking loops should be asynced or something
        # Add error handling to this
        status = None
        trys = 0
        while status != "running":
            trys += 1
            status = self.nomad_client.job[job_id]["Status"]
            if trys > 1000:
                raise BoxError(detail="The box failed to start.")

        job_info = self.nomad_client.job.get_allocations(job_id)

        allocation_info = self.nomad_client.allocation.get_allocation(
            dig(job_info, "0/ID")
        )

        allocation_node = values(allocation_info, "NodeID")
        nodes = self.nomad_client.nodes.get_nodes()

        ip_address = next(x["Address"] for x in nodes if x["ID"] in allocation_node)
        allocated_ports = values(allocation_info, "Resources/Networks/0/DynamicPorts/*")
        ssh_port = next(x for x in allocated_ports if x["Label"] == "ssh")["Value"]
        if current_app.config["ENV"] == "development":
            ip_address = current_app.config["SEA_HOST"]

        return (ssh_port, ip_address)


class BoxDeletionService:
    def __init__(self, current_user: User, box: Optional[Box], job_id=None):
        self.current_user = current_user
        self.box = box
        if job_id:
            self.job_id = job_id
        if box:
            self.config = box.config
            self.job_id = box.job_id

        self.nomad_client = nomad.Nomad(discover_service("nomad").ip)

    def delete(self):
        db.session.delete(self.box)
        db.session.delete(self.config)
        db.session.flush()
        cleanup_old_nomad_box.queue(self.job_id, timeout=60000)
