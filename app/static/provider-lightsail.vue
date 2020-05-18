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
              v-model="aws_secret_key">
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
      aws_secret_key: null
    };
  },
  computed: {
    is_valid() {
      return this.aws_access_key && this.aws_secret_key;
    }
  },
  methods: {
    submit() {
      this.$emit('submit', {
        aws_access_key: this.aws_access_key,
        aws_secret_key: this.aws_secret_key
      });
    }
  }
};
</script>
