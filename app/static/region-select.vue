<template>
  <div class="form-group">
    <label v-if="ui_show_slot"><slot></slot></label>
    <label v-if="ui_show_loading">Loading regions...</label>
    <label v-if="ui_show_select_prompt"
      >What region should the server be located in?</label
    >
    <select
      name="region"
      class="form-control"
      v-bind:class="{ 'is-invalid': has_error }"
      v-bind:value="value"
      v-bind:disabled="ui_disabled"
      v-on:input="$emit('input', $event.target.value)"
    >
      <option value disabled>Select region</option>
      <option
        v-for="(region, i) in options"
        v-bind:key="i"
        v-bind:value="region.key"
        >{{ region.value }}</option
      >
    </select>
    <div v-if="has_error" class="invalid-feedback">
      There was an error during fetching regions
    </div>
  </div>
</template>

<script>
module.exports = {
  props: ["value", "options", "loading", "error"],
  computed: {
      has_options: function() {
        return this.options && this.options.length;
      },
      ui_disabled: function() {
          return !this.has_options || this.loading;
      },
      ui_show_slot: function() {
          return !this.loading && !this.has_options
      },
      ui_show_loading: function() {
          return this.loading;
      },
      ui_show_select_prompt: function() {
          return this.has_options;
      },
      has_error: function() {
          return !!this.error;
      }
  }
};
</script>
