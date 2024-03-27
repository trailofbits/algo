<template>
  <div>
    <div class="form-group">
      <label for="id_server">
          Enter the IP address of your server: (or use localhost for local installation):
      </label>
      <input
        type="text"
        class="form-control"
        id="id_server"
        name="server"
        v-model="server"
      />
    </div>
    <div class="form-group">
      <label for="id_ssh_user">
          What user should we use to login on the server? (note: passwordless login required, or ignore if you're deploying to localhost)
      </label>
      <input
        type="text"
        class="form-control"
        id="id_ssh_user"
        name="ssh_user"
        v-model="ssh_user"
      />
    </div>
    <div class="form-group">
      <label for="id_endpoint">
          Enter the public IP address or domain name of your server: (IMPORTANT! This is used to verify the certificate)
      </label>
      <input
        type="text"
        class="form-control"
        id="id_endpoint"
        name="endpoint"
        v-model="endpoint"
      />
    </div>
    <button v-on:click="submit"
      v-bind:disabled="!is_valid" class="btn btn-primary" type="button">Next</button>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      server: null,
      ssh_user: null,
      endpoint: null
    }
  },
  computed: {
    is_valid() {
      return this.server && this.ssh_user && this.endpoint;
    }
  },
  methods: {
    submit() {
      this.$emit("submit", {
        server: this.server,
        ssh_user: this.ssh_user,
        endpoint: this.endpoint
      });
    }
  }
};
</script>
