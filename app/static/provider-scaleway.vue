<template>
  <div>

    <div class="form-group">
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
        v-bind:disabled="ui_loading_check || ui_token_from_env"
        v-model="scaleway_token"
      />
      <p v-if="ui_token_from_env">Token was read from the environment</p>
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
      ui_token_from_env: false,
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
      return this.region && (this.scaleway_token || this.ui_token_from_env);
    }
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      fetch("/scaleway_config")
        .then(r => r.json())
        .then(response => {
          if (response.ok) {
            this.ui_token_from_env = true;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    submit() {
      if (this.ui_token_from_env) {
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