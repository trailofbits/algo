<template>
  <div>
    <div class="form-group">
      <label for="id_do_token">
          Enter your API token. The token must have read and write permissions
          (<a href="https://cloud.digitalocean.com/settings/api/tokens" target="_blank" rel="noopener noreferrer">https://cloud.digitalocean.com/settings/api/tokens</a>):
      </label>
      <input
          type="text"
          class="form-control"
          id="id_do_token"
          name="do_token"
          v-model="do_token"
          @blur="load_do_regions"
      />
    </div>
    <div class="form-group">
      <label
          v-if="do_regions.length > 0"
          for="id_region"
      >What region should the server be located in?</label>
      <label
          v-if="do_regions.length === 0"
          for="id_region"
      >Please enter API key above to select region</label>
      <label v-if="do_region_loading" for="id_region">Loading regions...</label>
      <select
          name="region"
          id="id_region"
          class="form-control"
          v-model="do_region"
          v-bind:disabled="do_region_loading"
      >
          <option value disabled>Select region</option>
          <option
            v-for="(region, i) in do_regions"
            v-bind:key="region.slug"
            v-bind:value="region.slug"
            >{{region.name}}</option>
      </select>
    </div>
    <button @click="submit" v-bind:disabled="!do_region" class="btn btn-primary" type="button">Next</button>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      do_token: null,
      do_region: null,
      do_regions: [],
      do_region_loading: false
    }
  },
  methods: {
    load_do_regions: function () {
      this.do_region_loading = true;
        fetch('https://api.digitalocean.com/v2/regions', {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.do_token}`
          }
        })
          .then(r => r.json())
          .then(r => {
            this.do_regions = r.regions;
          })
          .finally(() => {
            this.do_region_loading = false;
          });
    },
    submit() {
      this.$emit('submit', {
        do_token: this.do_token,
        region: this.do_region
      })
    }
  }
};
</script>
