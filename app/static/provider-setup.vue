<template>
  <div class="row" id="prodiver_id">
    <h2 class="col-12">
      <button type="button" class="btn btn-secondary back-button" v-on:click="$emit('back')"><</button>
      <span v-if="provider">{{ provider.name }} Setup</span>
      <span v-else>Select cloud provider</span>
    </h2>
    <div class="col-4">
      <ul class="nav flex-column nav-pills">
        <li class="nav-item"
          v-for="item in providers_map"
          v-bind:key="item.alias">
          <a
            class="nav-link"
            href="#prodiver_id"
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
  methods: {
    set_provider(provider) {
      this.provider = provider;
    },
    on_provider_submit(extra_args) {
      this.$emit('submit', Object.assign({provider: this.provider.alias}, extra_args));
    }
  },
  components: {
    'digitalocean': window.httpVueLoader('/static/provider-do.vue')
  }
};
</script>
<style scoped>
.back-button {
  position: absolute;
  border-radius: 50%;
  left: -2em;
}
</style>
