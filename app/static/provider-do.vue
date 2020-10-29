<template>
  <div>
    <div class="form-group">
      <label for="id_do_token">
          Enter your API token. The token must have read and write permissions
          <a href="https://cloud.digitalocean.com/settings/api/tokens" title="https://cloud.digitalocean.com/settings/api/tokens" class="badge bagde-pill badge-primary" target="_blank" rel="noopener noreferrer">?</a>
      </label>
      <div v-if="ui_token_from_env">
        <input
          type="password"
          class="form-control"
          v-bind:disabled="ui_loading_check"
          v-bind:value="'1234567890abcdef'"
        />
        <div v-if="ui_token_from_env" class="form-text alert alert-success" role="alert">
          The token was read from the environment variable
        </div>
      </div>
      <div v-else>
        <input
          type="text"
          class="form-control"
          id="id_do_token"
          name="do_token"
          v-bind:disabled="ui_loading_check"
          v-model="do_token"
          @blur="load_regions"
        />
      </div>
      
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
      do_token: null,
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
      return (this.do_config || this.ui_token_from_env) && this.region;
    }
  },
  created: function() {
    this.check_config();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      return fetch("/do_config")
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
      if (this.ui_token_from_env || this.do_token) {
        this.ui_loading_regions = true;
        this.ui_region_error = null;
        const payload = this.ui_token_from_env ? {} : {
          token: this.do_token
        };
        fetch("/do_regions", {
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
            this.ui_region_options = data.regions.map(i => ({key: i.slug, value: i.name}));
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
          do_token: this.do_token,
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
