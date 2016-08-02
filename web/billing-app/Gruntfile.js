

module.exports = function (grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        static_js_dir: 'apps/static/js',
        static_css_dir: 'apps/static/css',
        assets_css_dir: 'apps/static/assets/css',
        assets_js_dir: 'apps/static/assets/js',

        concat: {

            app_css: {
                src: ['<%= static_css_dir %>/app.css', '<%= static_css_dir %>/stic*.css'],
                dest: '<%= assets_css_dir %>/app.css'
            },
            vendor_css: {
                src: ['<%= static_css_dir %>/libs/*.css'],
                dest: '<%= assets_css_dir %>/vendor.css'
            },
            menu_login_js: {
                src: ['<%= static_js_dir %>/controllers/cuControllers.js', '<%= static_js_dir %>/controllers/cuLogin*.js',
                    '<%= static_js_dir %>/services/login*','<%= static_js_dir %>/controllers/exportImportController.js'],
                dest: '<%= assets_js_dir %>/menu_login.js'
            },
            billing_js: {
                src: ['<%= static_js_dir %>/controllers/billing/*', '<%= static_js_dir %>/services/billing/*', '<%= static_js_dir %>/filters/*'],
                dest: '<%= assets_js_dir %>/billing.js'
            },
            quota_js: {
                src: ['<%= static_js_dir %>/services/billing/*','<%= static_js_dir %>/controllers/quota/*', '<%= static_js_dir %>/services/quota/*', '<%= static_js_dir %>/filters/*', '<%= static_js_dir %>/controllers/billing/*'],
                dest: '<%= assets_js_dir %>/quota.js'
            },
            usage_js: {
                src: ['<%= static_js_dir %>/services/usage/*','<%= static_js_dir %>/controllers/usage/*'],
                dest: '<%= assets_js_dir %>/usage.js'
            },
            instance_js: {
                src: ['<%= static_js_dir %>/services/instance/*','<%= static_js_dir %>/controllers/instance/*', '<%= static_js_dir %>/services/usage/*'],
                dest: '<%= assets_js_dir %>/instance.js'
            }


        },
        uglify: {
            options: {
                // the banner is inserted at the top of the output
                banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
            },
            dist: {
                files: {
                    'apps/static/assets/js/menu_login.min.js': ['<%= concat.menu_login_js.dest %>'],
                    'apps/static/assets/js/billing.min.js': ['<%= concat.billing_js.dest %>'],
                    'apps/static/assets/js/quota.min.js': ['<%= concat.quota_js.dest %>'],
                    'apps/static/assets/js/usage.min.js': ['<%= concat.usage_js.dest %>'],
                    'apps/static/assets/js/instance.min.js': ['<%= concat.instance_js.dest %>']
                }
            }
        },

        cssmin: {
            options: {
                shorthandCompacting: false,
                roundingPrecision: -1
            },
            target: {
                files: {
                    'apps/static/assets/css/app.min.css': ['<%= concat.app_css.dest %>'],
                    'apps/static/assets/css/vendor.min.css': ['<%= concat.vendor_css.dest %>']
                }
            }
        },
        // Deletes all .js files, but skips min.js files
        clean: {
            js: ["apps/static/assets/js/*.*", "apps/static/assets/css/*.*"]
        }
    });

    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
    grunt.loadNpmTasks('grunt-contrib-clean');

    grunt.registerTask('default', ['clean', 'concat', 'cssmin', 'uglify']);

};
