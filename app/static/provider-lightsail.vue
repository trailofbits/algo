<template>
  <div>
    <div v-if="ui_config_error && ui_config_error === 'missing_boto'" class="form-text alert alert-danger" role="alert">
      Python module "boto3" is missing, please install it to proceed
    </div>
    <div v-if="ui_env_secrets" class="form-text alert alert-success" role="alert">
      AWS credentials were read from the environment variables
    </div>
    <div v-else>
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
    </div>
    <region-select v-model="region"
      v-bind:options="ui_region_options"
      v-bind:loading="ui_loading_check || ui_loading_regions"
      v-bind:error="ui_region_error">
    </region-select>
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
      // ui helpoer variables
      ui_region_options: [],
      ui_env_secrets: null,
      ui_loading_check: false,
      ui_loading_regions: false,
      ui_config_error: null,
      ui_region_error: null
    };
  },
  computed: {
    has_secrets() {
      return this.ui_env_secrets || (this.aws_access_key && this.aws_secret_key);
    },
    is_valid() {
      return this.has_secrets && this.region;
    }
  },
  created: function() {
    this.check_config();
  },
  methods: {
    check_config() {
      this.ui_loading_check = true;
      fetch("/aws_config")
        .then(r => {
          if (r.status === 200 || r.status === 400) {
            return r.json();
          }
          throw new Error(r.status);
        })
        .then(response => {
          if (response.has_secret) {
            this.ui_env_secrets = true;
            this.load_regions();
          } else if (response.error) {
            this.ui_config_error = response.error;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    load_regions() {
      if (this.has_secrets && this.ui_region_options.length === 0) {
        this.ui_loading_regions = true;
        this.ui_region_error = false;
        const payload = this.ui_env_secrets ? {} : {
          aws_access_key: this.aws_access_key,
          aws_secret_key: this.aws_secret_key
        }
        fetch('/lightsail_regions', {
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
        .then(data => {
          this.ui_region_options = data.regions.map(i => ({key: i.name, value: i.displayName}));
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
      let submit_value = {
        region: this.region
      }
      if (!this.ui_env_secrets) {
        submit_value['aws_access_key'] = this.aws_access_key;
        submit_value['aws_secret_key'] = this.aws_secret_key;
      }
      this.$emit('submit', submit_value);
    }
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue"),
  }
};
</script>
