<template>
  <section class="text-center">
    <p>Set up usually takes 5-15 minutes</p>
    <p>You can close tab and open it again</p>
    <p>You can try to
      <button type="button" class="btn btn-link stop-button" v-on:click="$emit('submit')">STOP</button>
      setup and run it again
    </p>
    <p>Don’t close terminal!</p>
    <transition-group name="console" tag="div">
      <code class="console-item" v-for="(event, i) in last_n_events" v-bind:key="event.counter">[{{ event.counter }}]: {{ event.stdout }}</code>
    </transition-group>
  </section>
</template>

<script>
module.exports = {
  data: function () {
    return {
      events: []
    }
  },
  computed: {
    last_n_events() {
      return this.events.filter(ev => (ev.stdout)).slice(-6);
    }
  },
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
    check: function () {
      return fetch("/playbook")
          .then(r => r.json())
          .catch(() => {
            this.$emit('error');
          })
          .then(data => {
            this.events = data.events;
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
code {
  display: block;
  text-align: left;
}
.stop-button {
  color: red;
  text-decoration: underline;
}
</style>
