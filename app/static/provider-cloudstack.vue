<template>
  <div>
    <div v-if="ui_token_from_env">
      <div v-if="ui_token_from_env" class="form-text alert alert-success" role="alert">
        The config file was found on your system
      </div>
    </div>
    <div class="form-group" v-else>
      
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
      cs_config: null,
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
      return (this.ui_config_uploaded || this.ui_token_from_env) && this.region;
    }
  },
  created: function() {
    this.check_config();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      return fetch("/cloudstack_config")
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
      if (this.ui_token_from_env || this.cs_config) {
        this.ui_loading_regions = true;
        this.ui_region_error = null;
        const payload = this.ui_token_from_env ? {} : {
          token: this.cs_config
        };
        fetch("/cloudstack_regions", {
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
          cs_config: this.cs_config,
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
