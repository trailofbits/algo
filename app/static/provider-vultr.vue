<template>
  <div>
     <div v-if="ui_token_from_env" class="form-text alert alert-success" role="alert">
      Vultr config file was found in your system
    </div>
    <div v-else class="form-group">
      <label
        >Enter Vultr API Token, it will be saved in your system
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
        name="vultr_token"
        v-bind:disabled="ui_loading_check"
        v-model="ui_token"
        v-on:blur="save_config"
      />
      <div v-if="vultr_config" class="form-text alert alert-success" role="alert">
        The config file was saved on your system
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
      ui_token: null,
      ui_token_from_env: false,
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
      return this.ui_token_from_env || this.vultr_config;
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
            this.ui_token_from_env = true;
            this.load_regions();
          } else if (response.error) {
            this.ui_config_error = response.error;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    save_config() {
      this.ui_loading_check = true;
      fetch("/vultr_config", {
        method: 'post',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          token: this.ui_token
        })
      })
      .then(r => {
          if (r.status === 200 || r.status === 400) {
            return r.json();
          }
          throw new Error(r.status);
        })
        .then(response => {
          if ('saved_to' in response) {
            this.vultr_config = response.saved_to;
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
            key: data[k].DCID
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
      if (!this.ui_token_from_env) {
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