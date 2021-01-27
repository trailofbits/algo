<template>
  <div>
    <div v-if="ui_token_from_env">
      <div v-if="ui_token_from_env" class="form-text alert alert-success" role="alert">
        The token was read from the environment variable
      </div>
    </div>
    <div class="form-group" v-else>
      <label for="id_token">
          Enter your API token. The token must have read and write permissions
          <a href="https://github.com/trailofbits/algo/blob/master/docs/cloud-linode.md" title="https://github.com/trailofbits/algo/blob/master/docs/cloud-linode.md" class="badge bagde-pill badge-primary" target="_blank" rel="noopener noreferrer">?</a>
      </label>
      <input
        type="text"
        class="form-control"
        id="id_token"
        name="linode_token"
        v-bind:disabled="ui_loading_check"
        v-model="linode_token"
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
      linode_token: null,
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
      return (this.linode_token || this.ui_token_from_env) && this.region;
    }
  },
  created: function() {
    this.check_config();
    this.load_regions();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      return fetch("/linode_config")
        .then(r => r.json())
        .then(response => {
          if (response.has_secret) {
            this.ui_token_from_env = true;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    load_regions() {
      this.ui_loading_regions = true;
      this.ui_region_error = null;
      const payload = this.ui_token_from_env ? {} : {
        token: this.hcloud_token
      };
      fetch("/linode_regions")
        .then((r) => {
          if (r.status === 200) {
            return r.json();
          }
          throw new Error(r.status);
        })
        .then((data) => {
          this.ui_region_options = data.data.map(i => ({key: i.id, value: i.id}));
        })
        .catch((err) => {
          this.ui_region_error = err;
        })
        .finally(() => {
          this.ui_loading_regions = false;
        });
    },
    submit() {
      if (this.ui_token_from_env) {
        this.$emit("submit", {
          region: this.region
        });
      } else {
        this.$emit("submit", {
          linode_token: this.linode_token,
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
