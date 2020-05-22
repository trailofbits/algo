<template>
  <div>
    <div class="form-group">
      <label>
          Enter your AWS Access Key <a href="http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html" title="http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html" target="_blank" rel="noreferrer noopener" class="badge bagde-pill badge-primary">?</a>
        <br>
          Note: Make sure to use an IAM user with an acceptable policy attached (see <a
              href="https://github.com/trailofbits/algo/blob/master/docs/deploy-from-ansible.md" target="_blank" rel="noreferrer noopener" >docs</a>)
      </label>
      <input
          type="text"
          class="form-control"
          name="aws_access_key"
          v-on:blur="load_regions"
          v-model="aws_access_key"
      />
    </div>
    <div class="form-group">
      <label>Enter your AWS Secret Key <a
              href="http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html" title="http://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html" target="_blank" rel="noreferrer noopener" class="badge bagde-pill badge-primary">?</a></label>
      <input
              type="password"
              class="form-control"
              name="aws_secret_key"
              v-on:blur="load_regions"
              v-model="aws_secret_key">
    </div>
    <div class="form-group">
      <label v-if="lightsail_regions.length === 0">Please enter Access key and Secret key to select region</label>
      <label v-if="is_loading">Loading regions...</label>
      <label v-if="lightsail_regions.length > 0">What region should the server be located in?</label>
      <select name="region"
              class="form-control"
              v-model="region"
              v-bind:disabled="is_region_disabled">
          <option value disabled>Select region</option>
          <option
            v-for="(region, i) in lightsail_regions"
            v-bind:key="region.displayName"
            v-bind:value="region.name"
            >{{region.displayName}}</option>
      </select>

    </div>
    <button class="btn btn-primary"
            type="button"
            v-on:click="submit"
            v-bind:disabled="!is_valid">
      Next
    </button>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      aws_access_key: null,
      aws_secret_key: null,
      region: null,
      lightsail_regions: [],
      is_loading: false
    };
  },
  computed: {
    is_valid() {
      return this.aws_access_key && this.aws_secret_key && this.region;
    },
    is_region_disabled() {
      return !(this.aws_access_key && this.aws_secret_key) || this.is_loading;
    }
  },
  methods: {
    load_regions() {
      if (this.aws_access_key && this.aws_secret_key && this.lightsail_regions.length === 0) {
        this.is_loading = true;
        fetch('/lightsail_regions', {
          method: 'post',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            aws_access_key: this.aws_access_key,
            aws_secret_key: this.aws_secret_key
          })
        })
        .then(r => r.json())
        .then(data => {
          this.lightsail_regions = data.regions;
        })
        .finally(() => {
          this.is_loading = false;
        });
      }
    },
    submit() {
      this.$emit('submit', {
        aws_access_key: this.aws_access_key,
        aws_secret_key: this.aws_secret_key,
        region: this.region
      });
    }
  }
};
</script>
