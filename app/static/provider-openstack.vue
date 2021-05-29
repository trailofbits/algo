<template>
  <div>
    <p>
      Download OpenStack credentials from the OpenStack dashboard->Compute->API Access and source it in the shell (eg:
      source /tmp/dhc-openrc.sh)
    </p>
    <button v-on:click="submit" class="btn btn-primary" type="button">Next</button>
  </div>
</template>

<script>
module.exports = {
  methods: {
    submit() {
      this.$emit("submit");
    }
  }
};
</script>
