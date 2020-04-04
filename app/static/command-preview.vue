<template>
  <div class="row">
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
  .code {
    white-space: normal;
    background: black;
    color: lightgrey;
    padding: 1em;
  }
</style>
