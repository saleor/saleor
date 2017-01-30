module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    
    uglify: {
      dev: {
        files: {
          'themes/saleor/source/js/jquery.js': ['node_modules/jquery/dist/jquery.js'],
          'themes/saleor/source/js/app.js':[
            'node_modules/bootstrap-sass/assets/javascripts/bootstrap.js',
            'themes/saleor/js/app.js'
          ]
        }
      }
    },  
    sass: { 
      options: {
        includePaths: ['node_modules/bootstrap-sass/assets/stylesheets/']
      },                             
      dist: {                             
        options: {                       
          style: 'compressed'
        },
        files: {                         
          'themes/saleor/source/app.css': 'themes/saleor/styles/app.scss'
        }
      }
    },
    imagemin: {
      dynamic: {
        files: [{
          expand: true,
          cwd: 'themes/saleor/images',
          src: ['**/*.{png,jpg,gif,svg}'],
          dest: 'themes/saleor/source/images/'
        }]
      }
    },
    watch: {
      grunt: { files: ['Gruntfile.js'] },
      sass: {
        files: 'themes/saleor/styles/**/*.scss',
        tasks: ['sass']
      },
      uglify: {
        files: 'themes/saleor/js/*.js',
        tasks: ['uglify']
      }
    },
    browserSync: {
      dev: {
        bsFiles: {
          src : [
            'public/styles/*.css',
            'public/'
          ]
        },
        options: {
          watchTask: true,
          server: 'public'
        }
      }
    }  
  });

  grunt.loadNpmTasks('grunt-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-browser-sync');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-imagemin');

  grunt.registerTask('build', ['sass', 'uglify', 'imagemin']);
  grunt.registerTask('sync', ['browserSync','watch', 'uglify']);
};
