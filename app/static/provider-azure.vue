<template>
  <div>
    <div v-if="ui_config_error && ui_config_error === 'missing_requests'" class="form-text alert alert-danger" role="alert">
      Python module "requests" is missing, please install it to proceed
    </div>
    <div v-if="ui_config_error && ui_config_error === 'missing_azure'" class="form-text alert alert-danger" role="alert">
      Python Azure SDK libraries are missing, please install it to proceed
    </div>
    <div class="form-text alert alert-info" role="alert">
      <strong>Prerequisites:</strong> <a href="https://github.com/trailofbits/algo/blob/master/docs/cloud-azure.md"
                                         target="_blank" rel="noopener noreferrer">Install azure-cli</a>
    </div>
    <region-select v-model="region"
                   v-bind:options="ui_region_options"
                   v-bind:loading="ui_loading_check || ui_loading_regions"
                   v-bind:error="ui_region_error">
    </region-select>
    <button v-on:click="submit"
            v-bind:disabled="!is_valid" class="btn btn-primary" type="button">Next
    </button>
  </div>
</template>

<script>
module.exports = {
  data: function () {
    return {
      region: null,
      // helper variables
      ui_loading_check: false,
      ui_config_error: false,
      ui_loading_regions: false,
      ui_region_error: null,
      ui_region_options: []
    }
  },
  computed: {
    is_valid() {
      return !!this.region;
    }
  },
  created: function () {
    this.check_config();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      fetch("/azure_config")
          .then(r => {
            if (r.status === 200 || r.status === 400) {
              return r.json();
            }
            throw new Error(r.status);
          })
          .then(response => {
            if (response.status === 'ok') {
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
      this.ui_region_error = null;
      fetch("/azure_regions")
          .then((r) => {
            if (r.status === 200) {
              return r.json();
            }
            throw new Error(r.status);
          })
          .then((data) => {
            this.ui_region_options = data.map(i => ({key: i.name, value: i.displayName}));
          })
          .catch((err) => {
            this.ui_region_error = err;
          })
          .finally(() => {
            this.ui_loading_regions = false;
          });
    },
    submit() {
      this.$emit("submit", {
        region: this.region
      });
    }
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue"),
  }
};
</script>
