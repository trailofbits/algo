<template>
  <div>
    <div
      class="form-group dropzone"
      v-if="ui_needs_upload"
      v-on:dragover.prevent="dragover_handler"
      v-on:dragleave.prevent="dragleave_handler"
      v-on:drop.prevent="drop_handler"
      v-on:click="show_file_select"
      v-bind:class="{
        'dropzone--can-drop': ui_can_drop,
        'dropzone--error': ui_drop_error,
        'dropzone--success': ui_drop_success,
      }"
    >
      <strong>Drag your GCE config file or click here</strong>
      <p>
        File <code>configs/gce.json</code> was not found. Please create it (<a
          href="https://github.com/trailofbits/algo/blob/master/docs/cloud-gce.md"
          target="_blank"
          rel="noopener noreferrer"
          >how?</a
        >) or upload.
      </p>
      <p>After upload it <strong>will be saved</strong> in the configs folder.</p>
      <div v-if="ui_drop_error" class="alert alert-warning" role="alert">
        <strong>Error:</strong> {{ ui_drop_error }}.
      </div>

      <div v-if="ui_drop_success" class="alert alert-success" role="alert">
        <strong>{{ ui_drop_filename }} loaded successfully</strong>
      </div>
    </div>
    <input type="file" accept=".json,applciation/json" v-on:change="filechange_handler" />

    <div class="form-group">
      <region-select v-model="region" v-bind:options="ui_region_options" v-bind:loading="ui_loading_check || ui_loading_regions">
        <label>Please specify <code>gce.json</code> credentials file to select region</label>
      </region-select>
    </div>

    <button
      class="btn btn-primary"
      type="button"
      v-on:click="submit"
      v-bind:disabled="!is_valid"
    >
      Next
    </button>
  </div>
</template>

<script>
module.exports = {
  data: function () {
    return {
      drop_error: null,
      gce_credentials_file: null,
      region: null,
      // helper variables
      ui_can_drop: false,
      ui_drop_error: null,
      ui_drop_success: null,
      ui_drop_filename: null,
      ui_needs_upload: null,
      ui_loading_regions: false,
      ui_loading_check: false,
      ui_region_options: []
    };
  },
  created: function() {
    this.check_config();
  },
  computed: {
    is_valid() {
      return this.gce_credentials_file && this.region;
    }
  },
  methods: {
    show_file_select(e) {
      if (e.target.tagName === 'A') {
        return;
      }
      const input = this.$el.querySelector(['input[type=file]']);
      const event = new MouseEvent('click', {
        'view': window,
        'bubbles': true,
        'cancelable': true
      });
      input.dispatchEvent(event);
    },
    dragover_handler(e) {
      this.ui_can_drop = true;
      this.ui_drop_success = false;
      this.ui_drop_error = false;
      this.ui_drop_filename = null;
    },
    dragleave_handler() {
      this.ui_can_drop = false;
    },
    drop_handler(e) {
      try {
        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles.length !== 1) {
          this.ui_drop_error = 'Please upload GCE config as single file';
        }
        this.read_file(droppedFiles[0]);
      } catch (e) {
        this.ui_drop_error = 'Unhandled error while trying to read GCE config';
      }
    },
    filechange_handler(e) {
      if (e.target.files.length) {
        this.read_file(e.target.files[0]);
      }
    },
    read_file(file) {
        if (file.type !== 'application/json') {
          this.ui_drop_error = 'Incorrect file type';
        }
        const reader = new FileReader();
        reader.onload =  e => {
          let gce_config_content = null;
          try {
            gce_config_content = JSON.parse(e.target.result);
            this.ui_drop_success = true;
            this.ui_drop_filename = file.name;
            this.gce_credentials_file = 'configs/gce.json';
          } catch (e) {
            this.ui_drop_error = 'JSON format error';
          }
          gce_config_content && this.load_regions(gce_config_content);
        }
        reader.onerror =  e => {
          this.ui_drop_error = 'Error while reading file';
        }
        reader.readAsText(file);
      
    },
    check_config() {
      this.ui_loading_check = true;
      fetch("/gce_config")
        .then(r => r.json())
        .then(response => {
          if (response.status === 'ok') {
            this.gce_credentials_file = 'configs/gce.json';
            this.load_regions();
            this.ui_needs_upload = false;
          } else {
            this.ui_needs_upload = true;
          }
        })
        .finally(() => {
          this.ui_loading_check = false;
        });
    },
    load_regions(gce_config_content) {
      if (this.gce_credentials_file && this.ui_region_options.length === 0) {
        this.ui_loading_regions = true;
        fetch("/gce_regions", {
          method: "post",
          headers: {
            "Content-Type": "application/json",
          },
          body: gce_config_content ? JSON.stringify(gce_config_content) : '{}',
        })
          .then((r) => r.json())
          .then((data) => {
            this.ui_region_options = data.items.map(i => ({
              value: i.name,
              key: i.name
            }));
          })
          .finally(() => {
            this.ui_loading_regions = false;
          });
      }
    },
    submit() {
      this.$emit("submit", {
        gce_credentials_file: this.gce_credentials_file,
        region: this.region,
      });
    },
  },
  components: {
    "region-select": window.httpVueLoader("/static/region-select.vue"),
  },
};
</script>
<style scoped>
.dropzone {
  padding: 2em;
  border: 5px dotted #ccc;
  cursor: pointer;
}
input[type=file] {
  visibility: hidden;
}
.dropzone--can-drop {
  border-color: var(--blue);
}
.dropzone--error {
  border-color: var(--red);
}
.dropzone--success {
  border-color: var(--green);
}
</style>
