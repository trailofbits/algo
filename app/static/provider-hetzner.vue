<template>
  <div>
    <div v-if="ui_token_from_env">
      <div v-if="ui_token_from_env" class="form-text alert alert-success" role="alert">
        The token was read from the environment variable
      </div>
    </div>
    <div class="form-group" v-else>
      <label for="id_hcloud_token">
          Enter your API token. The token must have read and write permissions
          <a href="https://github.com/trailofbits/algo/blob/master/docs/cloud-hetzner.md" title="https://github.com/trailofbits/algo/blob/master/docs/cloud-hetzner.md" class="badge bagde-pill badge-primary" target="_blank" rel="noopener noreferrer">?</a>
      </label>
      <input
        type="text"
        class="form-control"
        id="id_hcloud_token"
        name="hcloud_token"
        v-bind:disabled="ui_loading_check"
        v-model="hcloud_token"
        @blur="load_regions"
      />
    </div>
    <region-select v-model="region"
      v-bind:options="ui_region_options"
      v-bind:loading="ui_loading_check || ui_loading_regions"
      v-bind:error="ui_region_error">
    </region-select>
    <button v-on:click="submit"
      v-bind:disabled="!is_valid" class="btn btn-primary" type="button">Next</button>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      hcloud_token: null,
      region: null,
      // helper variables
      ui_loading_check: false,
      ui_loading_regions: false,
      ui_region_error: null,
      ui_token_from_env: false,
      ui_region_options: []
    }
  },
  computed: {
    is_valid() {
      return (this.hcloud_config || this.ui_token_from_env) && this.region;
    }
  },
  created: function() {
    this.check_config();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      return fetch("/hetzner_config")
        .then(r => r.json())
        .then(response => {
          if (response.has_secret) {
            this.ui_token_from_env = true;
            this.load_regions();
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    load_regions() {
      if (this.ui_token_from_env || this.hcloud_token) {
        this.ui_loading_regions = true;
        this.ui_region_error = null;
        const payload = this.ui_token_from_env ? {} : {
          token: this.hcloud_token
        };
        fetch("/hetzner_regions", {
          method: 'post',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })
          .then((r) => {
            if (r.status === 200) {
              return r.json();
            }
            throw new Error(r.status);
          })
          .then((data) => {
            this.ui_region_options = data.datacenters.map(i => ({key: i.location.name, value: i.location.city}));
          })
          .catch((err) => {
            this.ui_region_error = err;
          })
          .finally(() => {
            this.ui_loading_regions = false;
          });
      }
    },
    submit() {
      if (this.ui_token_from_env) {
        this.$emit("submit", {
          region: this.region
        });
      } else {
        this.$emit("submit", {
          hcloud_token: this.hcloud_token,
          region: this.region
        });
      }
    }
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue"),
  }
};
</script>
