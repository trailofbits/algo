<template>
  <section class="text-center">
    <p>Set up usually takes 5-15 minutes</p>
    <p>You can close tab and open it again</p>
    <p>You can try to <button type="button" class="btn btn-link stop-button" v-on:click="$emit('submit')">STOP</button> setup and run it again</p>
    <p>Don’t close terminal!</p>
  </section>
</template>

<script>
module.exports = {
  created() {
    const loop = () => {
      this.check()
      .then(() => {
        setTimeout(loop, 5000);
      });
    };
    setTimeout(loop, 5000);
  },
  methods: {
    check: function() {
      return fetch("/playbook")
        .then(r => r.json())
        .catch(() => {
          this.$emit('error');
        })
        .then(data => {
          if (data.status && data.status === 'done') {
            this.$emit('done');
            throw new Error();
          }
          if (!data.status || data.status === 'cancelled') {
            this.$emit('cancelled');
            throw new Error();
          }
        });
    }
  }
}
</script>
<style scoped>
  .stop-button {
    color: red;
    text-decoration: underline;
  }
</style>
