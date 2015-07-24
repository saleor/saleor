module.exports = function(grunt) {
  grunt.initConfig({
    browserSync: {
      dev: {
        bsFiles: {
          src: [
            "static/*.css",
            "static/*.js",
            "*.html"
          ]
        },
        options: {
          open: false,
          port: "3004",
          server: {
            baseDir: "./"
          },
          reloadOnRestart: true,
          watchTask: true
        }
      }
    },
    jade: {
      release: {
        options: {
          data: {
            debug: false
          }
        },
        files: {
          "index.html": "src/jade/index.jade",
          "business.html": "src/jade/business.jade",
          "developers.html": "src/jade/developers.jade"
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
        src: "static/style.css"
      }
    },
    sass: {
      options: {
        sourceMap: true,
        includePaths: ["bower_components"]
      },
      dist: {
        files: {
          "static/style.css": "src/scss/style.scss"
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
          "static/site.js": [
            "bower_components/jquery/dist/jquery.js",
            "bower_components/bootstrap-sass/assets/javascripts/bootstrap.js",
            "bower_components/jquery-smooth-scroll/jquery.smooth-scroll.js",
            "bower_components/typed.js/js/typed.js",
            "src/js/site.js"
          ]
        }
      }
    },
    uncss: {
      dist: {
        files: {
          "static/style.css": "index.html"
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
      jade: {
        files: ["src/jade/**/*.jade"],
        tasks: ["jade"]
      },
      sass: {
        files: ["src/scss/**/*.scss"],
        tasks: ["sass", "postcss"]
      },
      uglify: {
        files: ["src/js/**/*.js"],
        tasks: ["uglify"]
      }
    }
  });

  require("load-grunt-tasks")(grunt);

  grunt.registerTask("default", ["sass", "uncss", "postcss", "uglify"]);
  grunt.registerTask("sync", ["browserSync", "watch"]);
};
