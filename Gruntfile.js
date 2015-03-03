module.exports = function(grunt) {
  grunt.initConfig({
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
            dest: "saleor/static/dist/fonts/",
            src: [
              "*"
            ]
          },
          {
            expand: true,
            dot: true,
            cwd: "saleor/static/components/components-font-awesome/fonts",
            dest: "saleor/static/dist/fonts/",
            src: [
              "*"
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
    }
  });

  grunt.loadNpmTasks("grunt-contrib-copy");
  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('default', ['copy', 'less']);
  grunt.registerTask('heroku', ['copy', 'less']);
};
