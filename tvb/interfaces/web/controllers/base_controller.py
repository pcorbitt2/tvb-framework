# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
The Main class in this file is initialized in web/run.py to be 
served on the root of the Web site.

This is the main UI entry point.

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import os
import cherrypy

from tvb.interfaces.web.controllers import common
from tvb.config import CONNECTIVITY_CLASS, CONNECTIVITY_MODULE
from tvb.basic.profile import TvbProfile
from tvb.basic.logger.builder import get_logger
from tvb.core.services.user_service import UserService
from tvb.core.services.flow_service import FlowService
from tvb.interfaces.web.controllers.decorators import using_template
from tvb.interfaces.web.structure import WebStructure

# Constants used be the mechanism that deletes files on disk
FILES_TO_DELETE_ATTR = "files_to_delete"


class BaseController(object):
    """
    This class contains the methods served at the root of the Web site.
    """


    def __init__(self):
        self.logger = get_logger(self.__class__.__module__)
        self.version_info = None

        self.user_service = UserService()
        self.flow_service = FlowService()

        analyze_category = self.flow_service.get_launchable_non_viewers()
        self.analyze_category_link = '/flow/step/' + str(analyze_category.id)
        self.analyze_adapters = None

        self.connectivity_tab_link = '/flow/step_connectivity'
        view_category = self.flow_service.get_visualisers_category()
        conn_id = self.flow_service.get_algorithm_by_module_and_class(CONNECTIVITY_MODULE, CONNECTIVITY_CLASS)[1].id
        connectivity_link = self.get_url_adapter(view_category.id, conn_id)

        self.connectivity_submenu = [dict(title="Large Scale Connectivity", subsection="connectivity",
                                          description="View Connectivity Regions. Perform Connectivity lesions",
                                          link=connectivity_link),
                                     dict(title="Local Connectivity", subsection="local",
                                          link='/spatial/localconnectivity/step_1/1',
                                          description="Create or view existent Local Connectivity entities.")]
        self.burst_submenu = [dict(link='/burst', subsection='burst',
                                   title='Simulation Cockpit', description='Manage simulations'),
                              dict(link='/burst/dynamic', subsection='dynamic',
                                   title='Phase plane', description='Configure model dynamics')]


    @staticmethod
    def mark_file_for_delete(file_name, delete_parent_folder=False):
        """
        This method stores provided file name in session, 
        and later on when request is done, all these files/folders
        are deleted
        
        :param file_name: name of the file or folder to be deleted
        :param delete_parent_folder: specify if the parent folder of the file should be removed too.
        """
        # No processing if no file specified
        if file_name is None:
            return

        files_list = common.get_from_session(FILES_TO_DELETE_ATTR)
        if files_list is None:
            files_list = []
            common.add2session(FILES_TO_DELETE_ATTR, files_list)

        # Now add file/folder to list
        if delete_parent_folder:
            folder_name = os.path.split(file_name)[0]
            files_list.append(folder_name)
        else:
            files_list.append(file_name)


    def _mark_selected(self, project):
        """
        Set the project passed as parameter as the selected project.
        """
        previous_project = common.get_current_project()
        ### Update project stored in selection, with latest Project entity from DB.
        members = self.user_service.get_users_for_project("", project.id)[1]
        project.members = members
        common.remove_from_session(common.KEY_CACHED_SIMULATOR_TREE)
        common.add2session(common.KEY_PROJECT, project)

        if previous_project is None or previous_project.id != project.id:
            ### Clean Burst selection from session in case of a different project.
            common.remove_from_session(common.KEY_BURST_CONFIG)
            ### Store in DB new project selection
            user = common.get_from_session(common.KEY_USER)
            if user is not None:
                self.user_service.save_project_to_user(user.id, project.id)
            ### Display info message about project change
            self.logger.debug("Selected project is now " + project.name)
            common.set_info_message("Your current working project is: " + str(project.name))


    @staticmethod
    def get_url_adapter(step_key, adapter_id, back_page=None):
        """
        Compute the URLs for a given adapter. 
        Same URL is used both for GET and POST.
        """
        result_url = '/flow/' + str(step_key) + '/' + str(adapter_id)
        if back_page is not None:
            result_url = result_url + "?back_page=" + str(back_page)
        return result_url


    @cherrypy.expose
    def index(self):
        """
        / Path response
        Redirects to /tvb
        """
        raise cherrypy.HTTPRedirect('/user')


    @cherrypy.expose()
    @using_template('user/base_user')
    def tvb(self, error=False, **data):
        """
        /tvb URL
        Returns the home page with the messages stored in the user's session.
        """
        self.logger.debug("Unused submit attributes:" + str(data))
        template_dictionary = dict(mainContent="../index", title="The Virtual Brain Project")
        template_dictionary = self._fill_user_specific_attributes(template_dictionary)
        if common.get_from_session(common.KEY_IS_RESTART):
            template_dictionary[common.KEY_IS_RESTART] = True
            common.remove_from_session(common.KEY_IS_RESTART)
        return self.fill_default_attributes(template_dictionary, error)


    @cherrypy.expose
    @using_template('user/base_user')
    def error(self, **data):
        """Error page to redirect when something extremely bad happened"""
        template_specification = dict(mainContent="../error", title="Error page", data=data)
        template_specification = self._fill_user_specific_attributes(template_specification)
        return self.fill_default_attributes(template_specification)


    def _populate_user_and_project(self, template_dictionary, escape_db_operations=False):
        """
         Populate the template dictionary with current logged user (from session).
         """
        logged_user = common.get_logged_user()
        template_dictionary[common.KEY_USER] = logged_user
        show_help = logged_user is not None and logged_user.is_online_help_active()
        template_dictionary[common.KEY_SHOW_ONLINE_HELP] = show_help

        project = common.get_current_project()
        template_dictionary[common.KEY_PROJECT] = project
        if project is not None and not escape_db_operations:
            self.update_operations_count()
        return template_dictionary


    @staticmethod
    def _populate_message(template_dictionary):
        """
         Populate the template dictionary with current message stored in session. 
         Also specify the message type (default INFO).
         Clear from session current message (to avoid displaying it twice).
         """
        msg = common.pop_message_from_session()
        template_dictionary.update(msg)
        return template_dictionary


    def _populate_menu(self, template_dictionary):
        """
        Populate current template with information for the Left Menu.
        """
        if common.KEY_FIRST_RUN not in template_dictionary:
            template_dictionary[common.KEY_FIRST_RUN] = False
        template_dictionary[common.KEY_LINK_ANALYZE] = self.analyze_category_link
        template_dictionary[common.KEY_LINK_CONNECTIVITY_TAB] = self.connectivity_tab_link
        if common.KEY_BACK_PAGE not in template_dictionary:
            template_dictionary[common.KEY_BACK_PAGE] = False
        template_dictionary[common.KEY_SECTION_TITLES] = WebStructure.WEB_SECTION_TITLES
        template_dictionary[common.KEY_SUBSECTION_TITLES] = WebStructure.WEB_SUBSECTION_TITLES
        return template_dictionary


    def _populate_section(self, algo_group, result_template, is_burst=True):
        """
        Populate Section and Sub-Section fields from current Algorithm-Group.
        """
        if algo_group.module == CONNECTIVITY_MODULE:
            result_template[common.KEY_SECTION] = 'connectivity'
            result_template[common.KEY_SUB_SECTION] = 'connectivity'
            result_template[common.KEY_SUBMENU_LIST] = self.connectivity_submenu

        elif algo_group.group_category.display:
            ## We are having a visualizer:
            if is_burst:
                result_template[common.KEY_SECTION] = 'burst'
                result_template[common.KEY_SUBMENU_LIST] = self.burst_submenu
            else:
                result_template[common.KEY_SECTION] = 'project'
            result_template[common.KEY_SUB_SECTION] = 'view_' + algo_group.subsection_name

        elif algo_group.group_category.rawinput:
            ### Upload algorithms
            result_template[common.KEY_SECTION] = 'project'
            result_template[common.KEY_SUB_SECTION] = 'data'

        elif 'RAW_DATA' in algo_group.group_category.defaultdatastate:
            ### Creators
            result_template[common.KEY_SECTION] = 'stimulus'
            result_template[common.KEY_SUB_SECTION] = 'stimulus'

        else:
            ### Analyzers
            result_template[common.KEY_SECTION] = algo_group.group_category.displayname.lower()
            result_template[common.KEY_SUB_SECTION] = algo_group.subsection_name
            result_template[common.KEY_SUBMENU_LIST] = self.analyze_adapters


    def _fill_user_specific_attributes(self, template_dictionary):
        """
        Attributes needed for base_user template.
        """
        template_dictionary[common.KEY_INCLUDE_TOOLTIP] = False
        template_dictionary[common.KEY_WRAP_CONTENT_IN_MAIN_DIV] = True
        template_dictionary[common.KEY_CURRENT_TAB] = 'none'

        return template_dictionary


    def fill_default_attributes(self, template_dictionary, escape_db_operations=False):
        """
        Fill into 'template_dictionary' data that we want to have ready in UI.
        """
        template_dictionary = self._populate_user_and_project(template_dictionary, escape_db_operations)
        template_dictionary = self._populate_message(template_dictionary)
        template_dictionary = self._populate_menu(template_dictionary)

        if common.KEY_ERRORS not in template_dictionary:
            template_dictionary[common.KEY_ERRORS] = {}
        if common.KEY_FORM_DATA not in template_dictionary:
            template_dictionary[common.KEY_FORM_DATA] = {}
        if common.KEY_SUB_SECTION not in template_dictionary and common.KEY_SECTION in template_dictionary:
            template_dictionary[common.KEY_SUB_SECTION] = template_dictionary[common.KEY_SECTION]
        if common.KEY_SUBMENU_LIST not in template_dictionary:
            template_dictionary[common.KEY_SUBMENU_LIST] = None

        template_dictionary[common.KEY_CURRENT_VERSION] = TvbProfile.current.version.BASE_VERSION
        template_dictionary[common.KEY_CURRENT_JS_VERSION] = TvbProfile.current.version.BASE_VERSION.replace(".", "")
        return template_dictionary


    def fill_overlay_attributes(self, template_dictionary, title, description, content_template,
                                css_class, tabs_horizontal=None, overlay_indexes=None, tabs_vertical=None):
        """
        This method prepares parameters for rendering overlay (overlay.html)
        
        :param title: overlay title
        :param description: overlay description
        :param content_template: path&name of the template file which will fill overlay content (without .html)
        :param css_class: CSS class to be applied on overlay 
        :param tabs_horizontal: list of strings containing names of the tabs spread horizontally
        :param tabs_vertical: list of strings containing names of the tabs spread vertically
        """
        if template_dictionary is None:
            template_dictionary = dict()

        template_dictionary[common.KEY_OVERLAY_TITLE] = title
        template_dictionary[common.KEY_OVERLAY_DESCRIPTION] = description
        template_dictionary[common.KEY_OVERLAY_CONTENT_TEMPLATE] = content_template
        template_dictionary[common.KEY_OVERLAY_CLASS] = css_class
        template_dictionary[common.KEY_OVERLAY_TABS_HORIZONTAL] = tabs_horizontal if tabs_horizontal is not None else []
        template_dictionary[common.KEY_OVERLAY_TABS_VERTICAL] = tabs_vertical if tabs_vertical is not None else []
        if overlay_indexes is not None:
            template_dictionary[common.KEY_OVERLAY_INDEXES] = overlay_indexes
        else:
            template_dictionary[common.KEY_OVERLAY_INDEXES] = range(len(tabs_horizontal)) \
                if tabs_horizontal is not None else []
        template_dictionary[common.KEY_OVERLAY_PAGINATION] = False

        return template_dictionary


    @cherrypy.expose
    @using_template('overlay_blocker')
    def showBlockerOverlay(self, **data):
        """
        Returns the content of the blocking overlay (covers entire page and do not allow any action)
        """
        return self.fill_default_attributes(dict(data))
    
    
    def update_operations_count(self):
        """
        If a project is selected, update Operation Numbers in call-out.
        """
        project = common.get_current_project()
        if project is not None:
            fns, sta, err, canceled, pending = self.flow_service.get_operation_numbers(project.id)
            project.operations_finished = fns
            project.operations_started = sta
            project.operations_error = err
            project.operations_canceled = canceled
            project.operations_pending = pending
            common.add2session(common.KEY_PROJECT, project)
            
                    
            
            
            