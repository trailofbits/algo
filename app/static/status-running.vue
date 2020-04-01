<template>
  <div class="row status-container">
    <h2 class="col-12"><span class="spin">🙃</span>Please be patient</h2>
    <section class="status-text">
      <p>VPN set up usually takes 5-15 minutes</p>
      <p>You can close tab and open it again</p>
      <p>You can try to <button type="button" class="btn btn-link back-button" v-on:click="$emit('submit')">STOP</button> setup and run it again</p>
      <p>Don’t close terminal!</p>
    </section>
  </div>
</template>

<script>
module.exports = {
  props: function() {
    // Warning: Mutable Object to edit partent props
    extra_args: Object
  },
  computed: {
    cli_preview() {
      return 'ansible-playbook main.yml --extra-vars "server_name=algo ondemand_cellular=true ondemand_wifi=true dns_adblocking=false ssh_tunneling=false store_pki=false ondemand_wifi_exclude=[] provider=digitalocean do_token=ad6b4405df208053e7b41e1c9e74b97364af1d6b902f6b6bb1d5575c52eca0c3 region=blr1"';
    }
  }
}
</script>
<style scoped>
  .back-button {
    color: red;
  }
  .status-container {
    display: flex;
    flex-direction: column;
  }
  .status-text {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .spin {
    animation-name: spin;
    animation-duration: 5000ms;
    animation-iteration-count: infinite;
    animation-timing-function: linear;

    display: block;
    animation-delay: 5s;
    width: 1em;
    height: 100%;
  }
  @keyframes spin {
    from {
      transform:rotate(0deg);
    }
    to {
      transform:rotate(360deg);
    }
  }
</style>
