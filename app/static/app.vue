<template>
  <div style="overflow: auto">
    <div class="container">
      <h1 class="mb-5 text-center">Algo VPN Setup</h1>
      <div class="row">
        <div class="col-md-4 order-md-2 mb-4" id="users_app">
          <h2>Users</h2>
          <section class="my-3">
            <h4>Set up user list</h4>
            <ul class="list-group">
              <li class="list-group-item" v-for="(user, index) in config.users" :key="user">
                {{ user }}
                <button
                  type="button"
                  class="btn btn-secondary btn-sm float-right"
                  @click="remove_user(index)"
                >Remove</button>
              </li>
            </ul>
            <div class="my-3 form-group">
              <label for="id_new_user">Add new user</label>
              <div class="input-group">
                <input
                  type="text"
                  id="id_new_user"
                  class="form-control"
                  placeholder="username"
                  v-model="new_user"
                />
                <div class="input-group-append">
                  <button
                    @click="add_user"
                    class="btn btn-outline-primary"
                    type="button"
                    id="button-addon2"
                  >Add</button>
                </div>
              </div>
            </div>
          </section>
          <div>
            <button
              @click="save_config"
              v-bind:disabled="loading"
              class="btn btn-secondary"
              type="button"
            >Save</button>
            <span
              v-if="save_config_message"
              v-bind:class="{ 'text-success': ok, 'text-danged': !ok }"
            >{{save_config_message}}</span>
          </div>
        </div>
        <div class="col-md-8 order-md-1" id="options_app">
          <h2>VPN Options</h2>
          <section class="my-3">
            <div class="form-group">
              <label>Name the vpn server</label>
              <input
                type="text"
                class="form-control"
                placeholder="server name"
                v-model="extra_args.server_name"
              />
            </div>
            <label>MacOS/iOS IPsec clients to enable Connect On Demand:</label>
            <div class="form-check">
              <label
                title="MacOS/iOS IPsec clients to enable Connect On Demand when connected to cellular
                            networks?"
              >
                <input
                  class="form-check-input"
                  type="checkbox"
                  name="ondemand_cellular"
                  v-model="extra_args.ondemand_cellular"
                />
                when connected to cellular networks
              </label>
            </div>
            <div class="form-check">
              <label
                title="MacOS/iOS IPsec clients to enable Connect On Demand when connected to Wi-Fi?"
              >
                <input
                  class="form-check-input"
                  type="checkbox"
                  name="ondemand_wifi"
                  v-model="extra_args.ondemand_wifi"
                />
                when connected to WiFi
              </label>
            </div>

            <div class="form-group">
              <label for="id_ondemand_wifi_exclude">Trusted Wi-Fi networks</label>
              <input
                type="text"
                class="form-control"
                id="id_ondemand_wifi_exclude"
                name="ondemand_wifi_exclude"
                placeholder="HomeNet,OfficeWifi,AlgoWiFi"
                v-model="extra_args.ondemand_wifi_exclude"
              />
              <small class="form-text text-muted">
                List the names of any trusted Wi-Fi networks where
                macOS/iOS
                IPsec clients should not use "Connect On Demand"
                (e.g., your home network. Comma-separated value, e.g.,
                HomeNet,OfficeWifi,AlgoWiFi)
              </small>
            </div>
            <label>Retain the PKI</label>
            <div class="form-check">
              <label>
                <input
                  class="form-check-input"
                  type="checkbox"
                  name="store_pki"
                  v-model="extra_args.store_pki"
                />
                Do you want to retain the keys (PKI)?
                <small
                  class="form-text text-muted"
                >
                  required to add users in the future, but less
                  secure
                </small>
              </label>
            </div>
            <label>DNS adblocking</label>
            <div class="form-check">
              <label>
                <input
                  class="form-check-input"
                  type="checkbox"
                  name="dns_adblocking"
                  v-model="extra_args.dns_adblocking"
                />
                Enable DNS ad blocking on this VPN server
              </label>
            </div>
            <label>SSH tunneling</label>
            <div class="form-check">
              <label>
                <input
                  class="form-check-input"
                  type="checkbox"
                  name="ssh_tunneling"
                  v-model="extra_args.ssh_tunneling"
                />
                Each user will have their own account for SSH tunneling
              </label>
            </div>
          </section>
        </div>
      </div>
      <hr class="my-3" />
      <section class="my-3" id="provider_app">
        <h2>Select cloud provider</h2>
        <div class="row">
          <div class="col-4">
            <ul class="nav flex-column nav-pills">
              <li class="nav-item" v-for="provider in providers_map">
                <a
                  class="nav-link"
                  href="#"
                  v-bind:class="{ active: provider.alias === extra_args.provider }"
                  @click="set_provider(provider.alias)"
                >{{provider.name}}</a>
              </li>
            </ul>
          </div>
          <div class="col-8">
            <div class="my-3" v-if="extra_args.provider === 'digitalocean'">
              <h4>Digital Ocean Options</h4>
              <div class="form-group">
                <label for="id_do_token">
                  Enter your API token. The token must have read and write permissions
                  (https://cloud.digitalocean.com/settings/api/tokens):
                </label>
                <input
                  type="text"
                  class="form-control"
                  id="id_do_token"
                  name="do_token"
                  v-model="extra_args.do_token"
                  @blur="load_do_regions"
                />
              </div>
              <div class="form-group">
                <label
                  v-if="do_regions.length > 0"
                  for="id_region"
                >What region should the server be located in?</label>
                <label
                  v-if="do_regions.length === 0"
                  for="id_region"
                >Please enter API key above to select region</label>
                <label v-if="do_region_loading" for="id_region">Loading regions...</label>
                <select
                  name="region"
                  id="id_region"
                  class="form-control"
                  v-model="extra_args.region"
                  v-bind:disabled="do_region_loading"
                >
                  <option value disabled>Select region</option>
                  <option
                    v-for="(region, index) in do_regions"
                    v-bind:value="region.slug"
                  >{{region.name}}</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
  <footer class="footer mt-auto py-3" id="status_app">
    <div
      class="backdrop d-flex flex-column align-items-center justify-content-center"
      v-if="show_backdrop"
    >
      <span class="spinner-border" role="status" aria-hidden="true"></span>
    </div>
    <div class="container">
      <div v-if="!status || status === 'cancelled'">
        <pre class="console">{{cli_preview}}</pre>
        <button @click="run" class="btn btn-primary" type="button">Install</button>
      </div>
      <div v-if="status === 'running'">
        <pre class="console">{{program.join(' ')}}</pre>
        <button class="btn btn-danger" type="button" @click="stop">Stop</button>
        <button class="btn btn-primary" type="button" disabled>
          <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
          Running...
        </button>
      </div>
      <div v-if="status === 'done'">
        <pre class="console">{{program.join(' ')}}</pre>
        <div v-if="is_success" class="text-success">Done!</div>
        <div v-else class="text-danger">Failed!</div>
      </div>
    </div>
  </footer>
</template>

<script>

var vpn_options_extra_args = {
  server_name: "algo",
  ondemand_cellular: false,
  ondemand_wifi: false,
  dns_adblocking: false,
  ssh_tunneling: false,
  store_pki: false,
  ondemand_wifi_exclude: ""
};

new Vue({
  el: "#options_app",
  data: {
    extra_args: vpn_options_extra_args
  }
});

var provider_extra_args = {
  provider: null
};

new Vue({
  el: "#provider_app",
  data: {
    loading: false,
    do_region_loading: false,
    do_regions: [],
    extra_args: provider_extra_args,
    providers_map: [
      { name: "DigitalOcean", alias: "digitalocean" },
      { name: "Amazon Lightsail", alias: "lightsail" },
      { name: "Amazon EC2", alias: "ec2" },
      { name: "Microsoft Azure", alias: "azure" },
      { name: "Google Compute Engine", alias: "gce" },
      { name: "Hetzner Cloud", alias: "hetzner" },
      { name: "Vultr", alias: "vultr" },
      { name: "Scaleway", alias: "scaleway" },
      { name: "OpenStack (DreamCompute optimised)", alias: "openstack" },
      { name: "CloudStack (Exoscale optimised)", alias: "cloudstack" },
      {
        name: "Install to existing Ubuntu 18.04 or 19.04 server (Advanced)",
        alias: "local"
      }
    ]
  },
  methods: {
    set_provider(provider) {
      this.extra_args.provider = provider;
    },
    load_do_regions: function() {
      if (
        this.extra_args.provider === "digitalocean" &&
        this.extra_args.do_token
      ) {
        this.loading = true;
        this.do_region_loading = true;
        fetch("/do/regions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ token: this.extra_args.do_token })
        })
          .then(r => r.json())
          .then(r => {
            this.do_regions = r.regions;
          })
          .finally(() => {
            this.loading = false;
            this.do_region_loading = false;
          });
      }
    }
  }
});

new Vue({
  el: "#status_app",
  data: {
    status: null,
    program: null,
    result: null,
    error: null,
    // shared data, do not write there
    vpn_options_extra_args,
    provider_extra_args
  },
  created() {
    this.loop = setInterval(this.get_status, 1000);
  },
  computed: {
    extra_args() {
      return Object.assign(
        {},
        this.vpn_options_extra_args,
        this.provider_extra_args
      );
    },
    cli_preview() {
      var args = "";
      for (arg in this.extra_args) {
        args += `${arg}=${this.extra_args[arg]} `;
      }
      return `ansible-playbook main.yml --extra-vars ${args}`;
    },
    show_backdrop() {
      return this.status === "running";
    },
    is_success() {
      return this.result === 0;
    }
  },
  watch: {
    status: function() {
      if (this.status === "done") {
        clearInterval(this.loop);
      }
    }
  },
  methods: {
    run() {
      fetch("/playbook", {
        method: "POST",
        body: JSON.stringify(this.extra_args),
        headers: {
          "Content-Type": "application/json"
        }
      });
    },
    stop() {
      fetch("/playbook", {
        method: "DELETE"
      });
    },
    get_status() {
      fetch("/playbook")
        .then(r => r.json())
        .then(status => {
          this.status = status.status;
          this.program = status.program;
          this.result = status.result;
        })
        .catch(err => {
          alert("Server error");
          clearInterval(this.loop);
        });
    }
  }
});
</script>

<style scoped>
.console {
  background: black;
  color: white;
  padding: 4px;
  border-radius: 2px;
  white-space: pre-line;
  padding-left: 2em;
  position: relative;
}
.console::before {
  content: "$";
  position: absolute;
  left: 1em;
}
.backdrop {
  position: fixed;
  background: white;
  opacity: 0.6;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  pointer-events: none;
}
.footer .container {
  position: relative;
  z-index: 101;
}
</style>
