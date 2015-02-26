module.exports = function(grunt) {
  grunt.initConfig({
    less: {
      production: {
        options: {
          compress: true,
          yuicompress: true,
          cleancss: true,
          optimization: 2
        },
        files: {
          "saleor/static/css/style.css": "saleor/static/less/style.less"
        }
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('default', ['less']);
  grunt.registerTask('heroku', ['less']);
};
