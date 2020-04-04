<template>
  <div>
    <h2>Users</h2>
    <section class="my-3">
      <h4>Set up user list</h4>
      <ul class="list-group">
        <li class="list-group-item" v-for="(user, index) in config.users" :key="user">
          {{ user }}
          <button
            type="button"
            class="btn btn-secondary btn-sm float-right"
            v-on:click="remove_user(index)"
          >Remove</button>
        </li>
      </ul>
      <div class="my-3 form-group">
        <label for="id_new_user">Add new user</label>
        <div class="input-group">
          <input
            type="text"
            id="id_new_user"
            class="form-control"
            placeholder="username"
            v-model="new_user"
          />
          <div class="input-group-append">
            <button
              v-on:click="add_user"
              class="btn btn-outline-primary"
              type="button"
              id="button-addon2"
            >Add</button>
          </div>
        </div>
      </div>
    </section>
    <div>
      <span
        v-if="save_config_message"
        v-bind:class="{ 'text-success': ok, 'text-danged': !ok }"
      >{{save_config_message}}</span>
    </div>
  </div>
</template>

<script>
module.exports = {
  data: function() {
    return {
      config: {},
      loading: false,
      new_user: "",
      save_config_message: ""
    };
  },
  created: function() {
    this.load_config();
  },
  methods: {
    add_user: function() {
      this.config.users.push(this.new_user);
      this.new_user = "";
      this.save_config();
    },
    remove_user: function(index) {
      this.config.users.splice(index, 1);
      this.save_config();
    },
    save_config: function() {
      if (this.loading) return;
      this.loading = true;
      fetch("/config", {
        method: "POST",
        body: JSON.stringify(this.config),
        headers: {
          "Content-Type": "application/json"
        }
      })
        .then(r => r.json())
        .then(result => {
          if (result.ok) {
            this.ok = true;
            this.save_config_message = "Saved!";
            setTimeout(() => {
              this.save_config_message = "";
            }, 1000);
          } else {
            this.ok = false;
            this.save_config_message = "Not Saved!";
            setTimeout(() => {
              this.save_config_message = "";
            }, 1000);
          }
        })
        .finally(() => {
          this.loading = false;
        });
    },
    load_config: function() {
      this.loading = true;
      fetch("/config")
        .then(r => r.json())
        .then(config => {
          this.config = config;
        })
        .finally(() => {
          this.loading = false;
        });
    }
  }
};
</script>
