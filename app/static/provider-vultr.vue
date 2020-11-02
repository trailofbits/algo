<template>
  <div>
    <div v-if="ui_env_secrets" class="form-text alert alert-success" role="alert">
      Vultr config file was found in your system
    </div>
    <div v-else class="form-group">
      <label
        >Enter the local path to your configuration INI file
        <a
          href="https://trailofbits.github.io/algo/cloud-vultr.html"
          title="https://trailofbits.github.io/algo/cloud-vultr.html"
          target="_blank"
          rel="noreferrer noopener"
          class="badge bagde-pill badge-primary"
          >?</a
        ></label
      >
      <input
        type="text"
        class="form-control"
        name="vultr_config"
        v-bind:disabled="ui_loading_check"
        v-model="vultr_config"
      />
      <div v-if="ui_env_secrets" class="form-text alert alert-success" role="alert">
        Configuration file was found in your system. You still can change the path to it
      </div>
    </div>

    <div class="form-group">
      <region-select v-model="region"
        v-bind:options="ui_region_options"
        v-bind:loading="ui_loading_check || ui_loading_regions">
      </region-select>
    </div>

    <button
      class="btn btn-primary"
      type="button"
      v-on:click="submit"
      v-bind:disabled="!is_valid"
    >
      Next
    </button>
  </div>
</template>

<script>
module.exports = {
  data: function () {
    return {
      vultr_config: null,
      region: null,
      // helper variables
      ui_env_secrets: false,
      ui_loading_check: false,
      ui_loading_regions: false,
      ui_region_options: []
    };
  },
  created: function() {
    this.check_config();
    this.load_regions();
  },
  computed: {
    has_secrets() {
      return this.ui_env_secrets || this.vultr_config;
    },
    is_valid() {
      return this.has_secrets && this.region;
    }
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      fetch("/vultr_config")
        .then(r => {
          if (r.status === 200 || r.status === 400) {
            return r.json();
          }
          throw new Error(r.status);
        })
        .then(response => {
          if (response.has_secret) {
            this.ui_env_secrets = true;
            this.load_regions();
          } else if (response.error) {
            this.ui_config_error = response.error;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    load_regions() {
      this.ui_loading_regions = true;
      fetch("/vultr_regions")
        .then((r) => r.json())
        .then((data) => {
          this.ui_region_options = Object.keys(data).map(k => ({
            value: data[k].name,
            key: data[k].name
          }));
        })
        .finally(() => {
          this.ui_loading_regions = false;
        });
    },
    submit() {
      let submit_value = {
        region: this.region
      }
      if (!this.ui_env_secrets) {
        submit_value['vultr_config'] = this.vultr_config;
      }
      this.$emit("submit", submit_value);
    },
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue"),
  }
};
</script>