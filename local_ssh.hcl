job "ssh-client" {
  datacenters = ["city"]

  type = "batch"

  parameterized {
    meta_required = ["ssh_key", "box_name", "base_url", "bandwidth"]
  }

  group "userland" {
    count = 1
    task "sshd" {
      driver = "docker"

      config {
        image = "cypherpunkarmory/box:develop"
        network_mode = "private-holes_default"

        labels {
          "io.userland.sshd" = "${NOMAD_META_BOX_NAME}"
        }

        port_map {
          ssh = 22
        }
      }

      env {
        "SSH_KEY" = "${NOMAD_META_SSH_KEY}"
        "BANDWIDTH" = "${NOMAD_META_BANDWIDTH}"
      }

      service {
        name = "box-${NOMAD_META_BOX_NAME}-ssh"

        port = "ssh"

        check {
          name = "ssh-${NOMAD_META_BOX_NAME}-up"
          address_mode = "driver"
          port = "ssh"
          type = "tcp"
          interval = "10s"
          timeout = "2s"
        }
      }

      resources {
        cpu    = 100 # MHz
        memory = 200 # MB

        network {
          mbits = 1

          # This requests a dynamic port named "http". This will
          # be something like "46283", but we refer to it via the
          # label "http".
          port "ssh" {}
        }
      }
    }
  }
}
