<template>
  <div>
    <section>
      <p>Config files and certificates are in the ./configs/ directory.</p>
      <p>Go to <a href="https://whoer.net/" target="_blank" rel="noopener noopener">https://whoer.net/</a>
        after connecting and ensure that all your traffic passes through the VPN.</p>
      <p v-if="result.local_service_ip">Local DNS resolver {{result.local_service_ip}}</p>
      <p v-if="result.p12_export_password">The p12 and SSH keys password for new users is <code>{{result.p12_export_password}}</code></p>
      <p v-if="result.CA_password">The CA key password is <code>{{result.CA_password}}</code></p>
      <p v-if="result.ssh_access">Shell access: <code>ssh -F configs/{{result.ansible_ssh_host}}/ssh_config {{config.server_name}}</code></p>
      <p>Read more on how to set up clients at the <a href="https://github.com/trailofbits/algo" target="_blank" rel="noopener noopener">Algo home page</a></p>
    </section>
    <section>
      <h2 class="text-center">Client configuration files</h2>
      <div v-for="user in config.users" :key="user">
        <h3>&#128100; {{user}}</h3>
        <div class="d-flex justify-content-between">
          <div v-if="config.wireguard_enabled">
            <p><strong>WireGuard</strong></p>
            <p>
              <img v-bind:src="`/results/${result.ansible_ssh_host}/wireguard/${user}.png`" alt="QR Code">
            </p>
            <p><a v-bind:href="`/results/${result.ansible_ssh_host}/wireguard/${user}.conf`">{{user}}.conf</a></p>
            <p>iOS <a v-bind:href="`/results/${result.ansible_ssh_host}/wireguard/apple/ios/${user}.mobileconfig`"> .mobileconfig</a>,
            Mac OS <a v-bind:href="`/results/${result.ansible_ssh_host}/wireguard/apple/macos/${user}.mobileconfig`"> .mobileconfig</a></p>
          </div>
          <div v-if="config.ipsec_enabled">
            <p><strong>IPSec</strong></p>
            <p>Apple's <a v-bind:href="`/results/${result.ansible_ssh_host}/ipsec/apple/${user}.mobileconfig`"> .mobileconfig</a></p>
            <p>Manual configuration:
              <a v-bind:href="`/results/${result.ansible_ssh_host}/ipsec/manual/${user}.conf`">{{user}}.conf</a>,
              <a v-bind:href="`/results/${result.ansible_ssh_host}/ipsec/manual/${user}.p12`">{{user}}.p12</a>,
              <a v-bind:href="`/results/${result.ansible_ssh_host}/ipsec/manual/${user}.secrets`">{{user}}.secrets</a>
            </p>
          </div>
        </div>
      </div>
    </section>
    <section>
      <h2 class="text-center">Finish setup and save configs</h2>
      <p class="text-center">
        <button v-on:click="$emit('submit')" class="btn btn-primary btn-lg" type="button">Save &amp; Exit</button>
      </p>
    </section>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      result: {},
      config: { users: [] }
    };
  },
  created() {
    fetch("/playbook")
      .then(r => r.json())
      .then(data => {
        this.result = data.result;
      });
    fetch("/config")
      .then(r => r.json())
      .then(data => {
        this.config = data;
      });
  }
}
</script>
