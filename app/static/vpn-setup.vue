<template>
  <div>
    <h2>VPN Options</h2>
    <section class="my-3">
      <div class="form-group">
        <label>Name the vpn server</label>
        <input
          type="text"
          class="form-control"
          placeholder="server name"
          v-model="extra_args.server_name"
        />
      </div>
      <label>MacOS/iOS IPsec clients to enable Connect On Demand:</label>
      <div class="form-check">
        <label
          title="MacOS/iOS IPsec clients to enable Connect On Demand when connected to cellular
                            networks?"
        >
          <input
            class="form-check-input"
            type="checkbox"
            name="ondemand_cellular"
            v-model="extra_args.ondemand_cellular"
          />
          when connected to cellular networks
        </label>
      </div>
      <div class="form-check">
        <label title="MacOS/iOS IPsec clients to enable Connect On Demand when connected to Wi-Fi?">
          <input
            class="form-check-input"
            type="checkbox"
            name="ondemand_wifi"
            v-model="extra_args.ondemand_wifi"
          />
          when connected to WiFi
        </label>
      </div>

      <div class="form-group">
        <label for="id_ondemand_wifi_exclude">Trusted Wi-Fi networks</label>
        <input
          type="text"
          class="form-control"
          id="id_ondemand_wifi_exclude"
          name="ondemand_wifi_exclude"
          placeholder="HomeNet,OfficeWifi,AlgoWiFi"
          v-model="extra_args.ondemand_wifi_exclude"
        />
        <small class="form-text text-muted">
          List the names of any trusted Wi-Fi networks where
          macOS/iOS
          IPsec clients should not use "Connect On Demand"
          (e.g., your home network. Comma-separated value, e.g.,
          HomeNet,OfficeWifi,AlgoWiFi)
        </small>
      </div>
      <label>Retain the PKI</label>
      <div class="form-check">
        <label>
          <input
            class="form-check-input"
            type="checkbox"
            name="store_pki"
            v-model="extra_args.store_pki"
          />
          Do you want to retain the keys (PKI)?
          <small class="form-text text-muted">
            required to add users in the future, but less
            secure
          </small>
        </label>
      </div>
      <label>DNS adblocking</label>
      <div class="form-check">
        <label>
          <input
            class="form-check-input"
            type="checkbox"
            name="dns_adblocking"
            v-model="extra_args.dns_adblocking"
          />
          Enable DNS ad blocking on this VPN server
        </label>
      </div>
      <label>SSH tunneling</label>
      <div class="form-check">
        <label>
          <input
            class="form-check-input"
            type="checkbox"
            name="ssh_tunneling"
            v-model="extra_args.ssh_tunneling"
          />
          Each user will have their own account for SSH tunneling
        </label>
      </div>
      <button v-on:click="$emit('submit')" class="btn btn-primary" type="button">Select Cloud Provider</button>
    </section>
  </div>
</template>

<script>
module.exports = {
  // Warning: Mutable Object to edit partent props
  props: ['extra_args']
}
</script>
