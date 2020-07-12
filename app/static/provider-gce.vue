<template>
  <div>
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
  data: function() {
    return {
      gce_credentials_file: null,
      region: null,
      // helper variables
      region_options: [],
      is_loading: false
    };
  },
  computed: {
    is_valid() {
      return this.gce_credentials_file && this.region;
    },
    is_region_disabled() {
      return !(this.gce_credentials_file) || this.is_loading;
    }
  },
  methods: {
    load_regions() {
      if (this.gce_credentials_file && this.region_options.length === 0) {
        this.is_loading = true;
        fetch('/gce_regions', {
          method: 'post',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            gce_credentials_file: this.gce_credentials_file
          })
        })
        .then(r => r.json())
        .then(data => {
          this.region_options = data;
        })
        .finally(() => {
          this.is_loading = false;
        });
      }
    },
    submit() {
      this.$emit('submit', {
        gce_credentials_file: this.gce_credentials_file,
        region: this.region
      });
    }
  }
};
</script>
