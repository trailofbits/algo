<template>
  <div class="row">
    <h2 class="col-12">
      <button type="button" class="btn btn-secondary back-button" v-on:click="$emit('back')"><</button>
      🧐 Review and Start!
    </h2>
    <section class="my-3">
      <pre class="code"><code>
        {{cli_preview}}
      </code></pre>
      <button v-on:click="$emit('submit')" class="btn btn-primary" type="button">Run!</button>
    </section>
  </div>
</template>

<script>
module.exports = {
  props: ['extra_args'],
  computed: {
    cli_preview: function() {
      let args = "";
      for (arg in this.extra_args) {
        args += `${arg}=${this.extra_args[arg]} `;
      }
      return `ansible-playbook main.yml --extra-vars ${args}`;
    }
  }
}
</script>
<style scoped>
  .back-button {
    position: absolute;
    border-radius: 50%;
    left: -2em;
  }
  .code {
    white-space: normal;
    background: black;
    color: lightgrey;
    padding: 1em;
  }
</style>
