<template>
  <div class="row">
    <div class="col-4">
      <ul class="nav flex-column nav-pills">
        <li class="nav-item"
          v-for="item in providers_map"
          v-bind:key="item.alias">
          <a
            class="nav-link"
            href="#"
            v-bind:class="{ active: item.alias === (provider && provider.alias) }"
            v-on:click="set_provider(item)"
          >{{item.name}}</a>
        </li>
      </ul>
    </div>
    <div class="col-8">
      <component v-if="provider" v-bind:is="provider.alias" v-on:submit="on_provider_submit"></component>
    </div>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      loading: false,
      provider: null,
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
    }
  },
  // Warning: Mutable Object to edit parent props
  props: ['extra_args'],
  methods: {
    set_provider(provider) {
      this.provider = provider;
      this.extra_args.provider = provider.alias;
    },
    on_provider_submit(extra_args) {
      Object.assign(this.extra_args, extra_args);
      this.$emit('submit');
    }
  },
  components: {
    'digitalocean': window.httpVueLoader('/static/provider-do.vue'),
    'lightsail': window.httpVueLoader('/static/provider-lightsail.vue'),
    'ec2': window.httpVueLoader('/static/provider-ec2.vue'),
    'gce': window.httpVueLoader('/static/provider-gce.vue'),
    'vultr': window.httpVueLoader('/static/provider-vultr.vue'),
    'scaleway': window.httpVueLoader('/static/provider-scaleway.vue')
  }
};
</script>
