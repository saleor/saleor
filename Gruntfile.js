module.exports = function(grunt) {
  grunt.initConfig({
    NODE_MODULES_DIR: 'node_modules/',
    STATIC_DIR: 'saleor/static/',
    webpack: {
      default: require('./webpack.config')
    },
    browserSync: {
      dev: {
        bsFiles: {
          src: [
            "<%= STATIC_DIR %>/css/*.css",
            "<%= STATIC_DIR %>/js/*.js",
            "saleor/**/*.html"
          ]
        },
        options: {
          open: false,
          port: "3004",
          proxy: "localhost:8000",
          reloadOnRestart: true,
          watchTask: true
        }
      }
    },
    copy: {
      address: {
        src: "saleor/static/js_src/address.json",
        dest: "saleor/static/js/address.json"
      },
      production: {
        files: [
          {
            expand: true,
            dot: true,
            cwd: "<%= NODE_MODULES_DIR %>/bootstrap-sass/assets/fonts/bootstrap",
            dest: "<%= STATIC_DIR %>/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "<%= NODE_MODULES_DIR %>/font-awesome/fonts",
            dest: "<%= STATIC_DIR %>/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "<%= NODE_MODULES_DIR %>/materialize-sass-origin/font/roboto",
            dest: "<%= STATIC_DIR %>/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "<%= NODE_MODULES_DIR %>/materialize-sass-origin/font/material-design-icons",
            dest: "<%= STATIC_DIR %>/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "<%= NODE_MODULES_DIR %>/dropzone/dist",
            dest: "<%= STATIC_DIR %>/scss/vendor/",
            src: [
              "*.css"
            ],
            rename: function(dest, src) {
              src = "_" + src;
              return dest + src.replace(/\.css$/, ".scss");
            }
          }
        ]
      }
    },
    postcss: {
      options: {
        map: true,
        processors: [
          require("autoprefixer")
        ]
      },
      prod: {
        src: [
          "<%= STATIC_DIR %>/css/storefront.css",
          "<%= STATIC_DIR %>/css/dashboard.css"
        ]
      }
    },
    sass: {
      options: {
        sourceMap: true,
        includePaths: ["<%= NODE_MODULES_DIR %>"]
      },
      dist: {
        files: {
          "<%= STATIC_DIR %>/css/storefront.css": "<%= STATIC_DIR %>/scss/storefront.scss",
          "<%= STATIC_DIR %>/css/dashboard.css": "<%= STATIC_DIR %>/scss/dashboard.scss"
        }
      }
    },
    watch: {
      options: {
        atBegin: true,
        interrupt: false,
        livereload: true,
        spawn: false
      },
      sass: {
        files: ["<%= STATIC_DIR %>/scss/**/*.scss"],
        tasks: ["sass", "postcss"]
      },
      uglify: {
        files: ["<%= STATIC_DIR %>/js_src/**/*.js", "<%= STATIC_DIR %>/js_src/**/*.jsx"],
        tasks: ["webpack"]
      }
    }
  });

  require("load-grunt-tasks")(grunt);

  grunt.registerTask("default", ["copy", "sass", "postcss", "webpack"]);
  grunt.registerTask("sync", ["browserSync", "watch"]);
  grunt.registerTask("heroku", ["copy", "sass", "postcss", "webpack"]);
};
