new Vue({
  el: '#users_app',
  data: {
    config: {},
    loading: false,
    new_user: '',
    save_config_message: ''
  },
  created: function() {
    this.load_config();
  },
  methods: {
    add_user: function() {
      this.config.users.push(this.new_user);
      this.new_user = '';
    },
    remove_user: function(index) {
      this.config.users.splice(index, 1);
    },
    save_config: function() {
      if (this.loading) return;
      this.loading = true;
      fetch('/config', {
        method: 'POST',
        body: JSON.stringify(this.config),
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(r => r.json())
        .then(result => {
          if (result.ok) {
            this.ok = true;
            this.save_config_message = 'Saved!';
            setTimeout(() => {
              this.save_config_message = '';
            }, 1000);
          } else {
            this.ok = false;
            this.save_config_message = 'Not Saved!';
            setTimeout(() => {
              this.save_config_message = '';
            }, 1000);
          }
        })
        .finally(() => {
          this.loading = false;
        });
    },
    load_config: function() {
      this.loading = true;
      fetch('/config')
        .then(r => r.json())
        .then(config => {
          this.config = config;
        })
        .finally(() => {
          this.loading = false;
        });
    }
  }
});

var vpn_options_extra_args = {
  server_name: 'algo',
  ondemand_cellular: false,
  ondemand_wifi: false,
  dns_adblocking: false,
  ssh_tunneling: false,
  store_pki: false,
  ondemand_wifi_exclude: ''
};

new Vue({
  el: '#options_app',
  data: {
    extra_args: vpn_options_extra_args
  }
});

var provider_extra_args = {
  provider: null
};

new Vue({
  el: '#provider_app',
  data: {
    loading: false,
    do_regions: [],
    extra_args: provider_extra_args,
    providers_map: [
      { name: 'DigitalOcean', alias: 'digitalocean' },
      { name: 'Amazon Lightsail', alias: 'lightsail' },
      { name: 'Amazon EC2', alias: 'ec2' },
      { name: 'Microsoft Azure', alias: 'azure' },
      { name: 'Google Compute Engine', alias: 'gce' },
      { name: 'Hetzner Cloud', alias: 'hetzner' },
      { name: 'Vultr', alias: 'vultr' },
      { name: 'Scaleway', alias: 'scaleway' },
      { name: 'OpenStack (DreamCompute optimised)', alias: 'openstack' },
      { name: 'CloudStack (Exoscale optimised)', alias: 'cloudstack' },
      {
        name: 'Install to existing Ubuntu 18.04 or 19.04 server (Advanced)',
        alias: 'local'
      }
    ]
  },
  methods: {
    set_provider(provider) {
      this.extra_args.provider = provider;
    },
    load_do_regions: function() {
      if (
        this.extra_args.provider === 'digitalocean' &&
        this.extra_args.do_token
      ) {
        this.loading = true;
        fetch('/do/regions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ token: this.extra_args.do_token })
        })
          .then(r => r.json())
          .then(r => {
            this.do_regions = r.regions;
          })
          .finally(() => {
            this.loading = false;
          });
      }
    }
  }
});

new Vue({
  el: '#status_app',
  data: {
    status: null,
    program: null,
    result: null,
    error: null,
    // shared data, do not write there
    vpn_options_extra_args,
    provider_extra_args,
  },
  created() {
    this.loop = setInterval(this.get_status, 1000);
  },
  computed: {
    extra_args() {
      return Object.assign({}, this.vpn_options_extra_args, this.provider_extra_args);
    },
    cli_preview() {
      var args = '';
      for (arg in this.extra_args) {
        args += `${arg}=${this.extra_args[arg]} `;
      }
      return `ansible-playbook main.yml --extra-vars ${args}`;
    },
    show_backdrop() {
      return this.status === 'running';
    }
  },
  watch: {
    status: function () {
      if (this.status === 'done') {
        clearInterval(this.loop);
      }
    }
  },
  methods: {
    run() {
      fetch('/playbook', {
        method: 'POST',
        body: JSON.stringify(this.extra_args),
        headers: {
          'Content-Type': 'application/json'
        }
      });
    },
    stop() {
      fetch('/playbook', {
        method: 'DELETE'
      });
    },
    get_status() {
      fetch('/playbook')
        .then(r => r.json())
        .then(status => {
          this.status = status.status;
          this.program = status.program;
          this.result = status.result;
        })
        .catch(err => {
          alert('Server error');
          clearInterval(this.loop);
        });
    }
  }
});
