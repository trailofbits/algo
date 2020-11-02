<template>
  <div>

    <div v-if="ui_env_secrets" class="form-text alert alert-success" role="alert">
      Token was read from the environment variable
    </div>
    <div v-else class="form-group">
      <label
        >Enter your auth token
        <a
          href="https://trailofbits.github.io/algo/cloud-scaleway.html"
          title="https://trailofbits.github.io/algo/cloud-scaleway.html"
          target="_blank"
          rel="noreferrer noopener"
          class="badge bagde-pill badge-primary"
          >?</a
        ></label
      >
      <input
        type="text"
        class="form-control"
        name="scaleway_token"
        v-bind:disabled="ui_loading_check"
        v-model="scaleway_token"
      />
    </div>
    <div class="form-group">
      <region-select v-model="region" v-bind:options="ui_region_options">
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
      scaleway_token: null,
      region: null,
      // helper variables
      ui_env_secrets: false,
      ui_loading_check: false,
      ui_region_options: [
        {value: 'Paris 1', key: 'par1'},
        {value: 'Amsterdam 1', key: 'ams1'}
      ]
    };
  },
  created: function() {
    this.check_config();
  },
  computed: {
    is_valid() {
      return this.region && (this.scaleway_token || this.ui_env_secrets);
    }
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      fetch("/scaleway_config")
        .then(r => {
          if (r.status === 200 || r.status === 400) {
            return r.json();
          }
          throw new Error(r.status);
        })
        .then(response => {
          if (response.has_secret) {
            this.ui_env_secrets = true;
          } else if (response.error) {
            this.ui_config_error = response.error;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    submit() {
      if (this.ui_env_secrets) {
        this.$emit("submit", {
          region: this.region
        });
      } else {
        this.$emit("submit", {
          scaleway_token: this.scaleway_token,
          region: this.region
        });
      }
    },
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue")
  },
};
</script>