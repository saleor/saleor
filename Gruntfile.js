module.exports = function(grunt) {
  grunt.initConfig({
    browserSync: {
      dev: {
        bsFiles: {
          src: [
            "saleor/static/css/*.css",
            "saleor/static/js/*.js",
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
      production: {
        files: [
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/bootstrap/dist/js/",
            dest: "saleor/static/dist/js/",
            src: [
              "bootstrap.min.js"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/bootstrap/fonts",
            dest: "saleor/static/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/components-font-awesome/fonts",
            dest: "saleor/static/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/materialize/font/roboto",
            dest: "saleor/static/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/materialize/font/material-design-icons",
            dest: "saleor/static/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/zocial-less/css",
            dest: "saleor/static/fonts/",
            src: [
              "zocial-regular-*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/less/dist/",
            dest: "saleor/static/dist/js/",
            src: [
              "less.min.js"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/jquery/dist/",
            dest: "saleor/static/dist/js/",
            src: [
              "jquery.min.*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/dropzone/dist",
            dest: "saleor/static/scss/vendor/",
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
    less: {
      production: {
        options: {
          compress: true,
          yuicompress: true,
          cleancss: true,
          optimization: 2
        },
        files: {
          "saleor/static/css/style.css": "saleor/static/less/style.less",
          "saleor/static/css/dashboard.css": "saleor/static/less/dashboard.less"
        }
      }
    },
    postcss: {
      options: {
        map: true,
        processors: [
          require("autoprefixer-core"),
          require("csswring")
        ]
      },
      prod: {
        src: "saleor/static/css/dashboard.css"
      }
    },
    sass: {
      options: {
        sourceMap: true,
        includePaths: ["saleor/static/components"]
      },
      dist: {
        files: {
          "saleor/static/css/dashboard.css": "saleor/static/scss/dashboard.scss"
        }
      }
    },
    uglify: {
      options: {
        mangle: false,
        sourceMap: true
      },
      dev: {
        files: {
          "saleor/static/js/dashboard.js": [
            "saleor/static/components/dropzone/dist/dropzone.js",
            "saleor/static/components/jquery/dist/jquery.js",
            "saleor/static/components/materialize/dist/js/materialize.js",
            "saleor/static/components/Sortable/Sortable.js",
            "saleor/static/components/select2/dist/js/select2.js",
            "saleor/static/js_src/dashboard.js",
            "saleor/static/components/dotdotdot/src/js/jquery.dotdotdot.js",
            "saleor/static/components/jquery.equalheights/jquery.equalheights.js"
          ],
          "saleor/static/js/dashboard-head.js": [
            "saleor/static/components/modernizr/modernizr.js"
          ]
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
        files: ["saleor/static/scss/**/*.scss"],
        tasks: ["sass", "postcss"]
      },
      uglify: {
        files: ["saleor/static/js_src/**/*.js"],
        tasks: ["uglify"]
      }
    }
  });

  require("load-grunt-tasks")(grunt);

  grunt.registerTask("default", ["copy", "less", "sass", "postcss", "uglify"]);
  grunt.registerTask("sync", ["browserSync", "watch"]);
  grunt.registerTask("heroku", ["copy", "less", "sass", "postcss", "uglify"]);
};
