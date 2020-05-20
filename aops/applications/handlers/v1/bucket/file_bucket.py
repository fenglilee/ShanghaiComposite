#!/usr/bin/env python
# -*- coding:utf-8 -*-

from flask import current_app as app
from flask import abort, request, session, send_file
from flask_restplus import Namespace, Resource, reqparse, Model, fields
from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.database.apis.bucket.bucket import get_file_list_from_scheduler, \
    trigger_mul_download_files, trigger_file_distributions, get_download_record_list, download_file_from_ftp
from aops.applications.exceptions.exception import ResourceNotFoundError, Error, SchedulerError, NotFoundFtpFileError
from aops.applications.handlers.v1.common import full_time_util, pagination_base_model
from aops.applications.database.apis.job.job_record import get_execution_record_list
from aops.applications.handlers.v1.job.job import execution_record_pagination_model


ns = Namespace('/v1/buckets', description='file buckets operations')

file_bucket_repository_model = Model('FileBucketItem', {
    'blob_id': fields.String(),
    'file_name': fields.String(required=True, description='The file\'s name'),
    'file_path': fields.String(required=True, description='The file path based on project /'),
    'ref': fields.String(required=True, default='blob', description='whether is directory or not'),
    'project_id': fields.Integer(required=True, description='The script\'s project id'),
    'content': fields.String(required=True, description='The script content'),
})

file_bucket_delete_file = Model('BucketDeleteFile', {
    'path': fields.String(),
    'type': fields.String()
})

file_distribution_model = Model('FileDistribution', {
    'id': fields.String(),
    'file_id': fields.Integer(),
    'path': fields.String(required=True, description='The file path based on project /'),
    'full_path': fields.String(required=True),
    'absolute_path': fields.String(required=True),
    'branch': fields.String(required=True),
    'type': fields.String(required=True, description='whether is directory or not'),
    'name': fields.String(),
    'update_user': fields.String(),
    'project_id': fields.Integer,
    'updated_at': fields.String(),
    'comment': fields.String()
})


host_files_model = Model("HostFilesModel", {
    'name': fields.String(description='file name'),
    'ctime': fields.Integer(description='create time'),
    "gr_name": fields.String(description="group name"),  # 所属组
    "isdir": fields.Boolean(description="whether is dir"),
    "islnk": fields.Boolean(description="whether is link file"),
    "mode": fields.String(description='file permission'),
    "mtime": fields.Integer(description='modified time'),
    "path": fields.String(description='file path'),
    "pw_name": fields.String(description="owner"),  # 所属用户
})


file_multiple_download_model = Model('FileMulDownload', {
    'target_ip': fields.List(fields.String),
    'path': fields.List(fields.String),
    'system_type': fields.String
})

ns.add_model(file_bucket_repository_model.name, file_bucket_repository_model)
ns.add_model(file_bucket_delete_file.name, file_bucket_delete_file)
ns.add_model(file_distribution_model.name, file_distribution_model)
ns.add_model(file_multiple_download_model.name, file_multiple_download_model)
ns.add_model(host_files_model.name, host_files_model)

file_bucket_args = reqparse.RequestParser()
file_bucket_args.add_argument('path')

file_distribution_args = file_bucket_args.copy()
file_distribution_args.add_argument('branch')

file_browser_args = file_bucket_args.copy()
file_browser_args.add_argument('ip', required=True)

"""download record"""
download_record_model = full_time_util.clone('DownloadRecord', {
    'id': fields.Integer(readOnly=True),
    'creator': fields.String(required=True),
    'execution_id': fields.String(required=False),
    'system_type': fields.String(required=True),
    'target_ip': fields.String(required=True),
    'success_ip': fields.String(required=True),
    'failed_ip': fields.String(required=True),
    'start_time': fields.DateTime(required=False),
    'status': fields.String(required=True),
    'business_group': fields.String(required=True),
})

download_record_pagination_model = pagination_base_model.clone('JobRecordPagination', {
    'items': fields.List(fields.Nested(download_record_model))
})


"""distribution record"""
distribution_record_model = full_time_util.clone('DistributionRecord', {
    'id': fields.Integer(readOnly=True),
    'creator': fields.String(required=True),
    'execution_id': fields.String(required=False),
    'execution_type': fields.String(required=True),
    'name': fields.String(required=True),
    'job_type': fields.String(required=True),
    'system_type': fields.String(required=True),
    'target_ip': fields.String(required=True),
    'start_time': fields.DateTime(required=False),
    'end_time': fields.DateTime(required=False),
    'status': fields.String(required=True),
    'result': fields.String(required=True),
    'time': fields.Integer(required=True),
    'business_group': fields.String(required=True),
})

distribution_record_pagination_model = pagination_base_model.clone('DistributionRecordPagination', {
    'items': fields.List(fields.Nested(distribution_record_model))
})

distribution_file_model = Model('DistributionFiles', {
    'project_id': fields.Integer(required=True),
    'full_path': fields.List(fields.String, required=True),
    'target_ip': fields.List(fields.String(required=True)),
    'target_dest': fields.String(description='host ip\'s dest directory'),
    'owner': fields.String(description='file\'s owner'),
    'mode': fields.String(description='file\'s permission'),
    'replace': fields.Boolean(description='whether replace file')
})

distribution_file_return_model = Model('DistributionFilesReturn', {
    'job_id': fields.String(required=True)
})

ns.add_model(download_record_model.name, download_record_model)
ns.add_model(download_record_pagination_model.name, download_record_pagination_model)
ns.add_model(distribution_file_model.name, distribution_file_model)
ns.add_model(distribution_file_return_model.name, distribution_file_return_model)


file_distribution_parser = reqparse.RequestParser()
file_distribution_parser.add_argument('project_id', type=int)
file_distribution_parser.add_argument('full_path', type=list, location='json')
file_distribution_parser.add_argument('target_ip', type=list, location='json', help='choose host ip')
file_distribution_parser.add_argument('target_dest', type=str, help='host ip\'s dest directory')
file_distribution_parser.add_argument('owner', type=str, help='file\'s owner')
file_distribution_parser.add_argument('mode', type=str, help='file\'s permission')
file_distribution_parser.add_argument('replace', type=bool, default=False, help='whether replace file')


file_record_list_args = reqparse.RequestParser()
file_record_list_args.add_argument('page', type=int, location='args', required=True, help='Current page number.')
file_record_list_args.add_argument('per_page', type=int, location='args', required=True,
                                   help='The number of items in a page.')

distribution_record_list_args = file_record_list_args.copy()
distribution_record_list_args.add_argument('job_type', location='args', help='job\'s type [distribution]')


download_record_list_args = file_record_list_args.copy()
# download_record_list_args.add_argument('creator', location='args', default='', help='default is linux')


file_multiple_download_args = reqparse.RequestParser()
file_multiple_download_args.add_argument('target_ip', type=list, required=True, location='json')
file_multiple_download_args.add_argument('path', type=list, required=True, location='json')
file_multiple_download_args.add_argument('system_type', type=str, required=False, default='linux')


@ns.route('/')
class FileBrowsers(Resource):
    """Repository Business Group list."""

    @ns.doc('file bucket repository info based on group_name')
    @ns.expect(file_distribution_args)
    @ns.marshal_list_with(file_distribution_model)
    def get(self):
        """Get repository file list base on path
        Returns:
            Gitlab repository items list.
        """
        try:
            args = file_distribution_args.parse_args()
            app.logger.debug(u"get file distributions with params: {}, ".format(args))
            file_list = Repostiory.get_file_distributions_list(args)
        except Error as e:
            app.logger.error(u"get file distributions, mgs: {}".format(e.msg))
            abort(e.code, e.msg)
        return file_list


@ns.route('/distributions')
class FileDistributions(Resource):
    """Repository file FileDistribution"""
    @ns.expect(distribution_record_list_args)
    @ns.marshal_list_with(execution_record_pagination_model)
    def get(self):
        """Repository files FileDistribution history list
        Returns:
            FileDistribution Process Status
        """
        try:
            args = distribution_record_list_args.parse_args()
            app.logger.debug(u"get file distributions with params: {}, ".format(args))
            trigger_status = get_execution_record_list(args.page, args.per_page, execution_type='instant',
                                                       job_type=args.job_type)
        except Error as e:
            app.logger.error(u"get file distributions, mgs: {}".format(e.msg))
            abort(e.code, e.msg)
        return trigger_status

    @ns.expect(distribution_file_model)
    @ns.marshal_list_with(distribution_file_return_model)
    def post(self):
        """Repository files FileDistribution
        Returns:
            FileDistribution's  execution_id
        """
        try:
            args = file_distribution_parser.parse_args()
            user_info = session.get('user_info')
            args.update(creator=user_info.get('user', 'god'))
            business_group = request.cookies.get('BussinessGroup', 'LDDS')
            args.update(business_group=business_group)
            args.update(execution_account='mds')
            app.logger.debug(u"trigger file distributions with params: {}, ".format(args))
            trigger_status = trigger_file_distributions(args)
        except Error as e:
            app.logger.error(u"trigger file distributions, mgs: {}".format(e.msg))
            abort(e.code, e.msg)
        return trigger_status


@ns.route('/hosts')
class FileBrowser(Resource):
    @ns.expect(file_browser_args)
    @ns.marshal_list_with(host_files_model)
    def get(self):
        """
        File Browser based on host and path.
        """
        try:
            args = file_browser_args.parse_args()
            args.update(system_type='linux')
            args.update(execution_account='mds')
            args.update(business_group=request.cookies.get('BusinessGroup', 'LDDS'))
            app.logger.debug("get host files with params: {}".format(args))
            files = get_file_list_from_scheduler(args)
        except SchedulerError as e:
            app.logger.error("get host files, msg: {}".format(e.msg))
            abort(e.code, e.msg)
        except ResourceNotFoundError as e:
            app.logger.error("Get host files, msg: {}".format(e.msg))
            abort(e.code, e.msg)
        return files


@ns.route('/mul-download')
class FileMulDownloads(Resource):
    """File Multiple Download."""
    """
    Shows a list of mul download type
    """
    @ns.doc('list_all_download_record')
    @ns.response(400, 'Validation Error')
    @ns.response(404, 'mul download record list not found')
    @ns.marshal_list_with(download_record_pagination_model)
    @ns.expect(download_record_list_args)
    def get(self):
        """
            list all download record
        Returns:
            all job record
        """
        args = download_record_list_args.parse_args()
        page = args.page
        per_page = args.per_page
        user_info = session.get('user_info', {'user': 'god'})
        creator = user_info.get('user')
        app.logger.debug("Get download record list's params are: {}, username: {}".format(args, creator))
        try:
            download_record = get_download_record_list(page, per_page, creator=creator)
            app.logger.info(
                u"Get mul-download record list's result with page num {}".format(page))
        except SchedulerError as e:
            app.logger.error(u"get file download list, msg: {}".format(e.msg))
            abort(e.code, e.msg)
        return download_record

    @ns.doc('file bucket multiple download')
    @ns.expect(file_multiple_download_model)
    @ns.marshal_list_with(download_record_model)
    def post(self):
        """
        Trigger async celery task file push to Ftp server
        Returns:

        """
        try:
            args = file_multiple_download_args.parse_args()
            app.logger.debug("download files async task with params: {}".format(args))
            business_group = request.cookies.get('BussinessGroup', 'LDDS')
            # TODO: creator get from session
            user_info = session.get('user_info', {'user': 'god'})
            creator = user_info.get('user')
            execution_account = 'mds'
            system_type = args.system_type if args.system_type else 'linux'
            files = trigger_mul_download_files(args, business_group, creator, execution_account, system_type)
        except SchedulerError as e:
            app.logger.error("download mul-files async task, msg: {}".format(e.msg))
            abort(e.code, e.msg)
        return files


@ns.route('/mul-download/<string:identifier>')
class FileMulDownload(Resource):
    """File Mul-Download's zip package download."""
    @ns.param('identifier', 'mul-download record\'s execution_id')
    def get(self, identifier):
        """
        Returns:  the file zip of download
        """
        try:
            zip_file_name, file_name = download_file_from_ftp(identifier)
        except NotFoundFtpFileError as e:
            app.logger.error(e.message)
            abort(e.code, e.message)
        except Error as e:
            app.logger.error("download files zip package failed, msg: {}".format(e.message))
            abort(e.code, e.message)
        # with open(zip_file_name, 'rb') as bites:
        #    return send_file(
        #        io.BytesIO(bites.read()),
        #        attachment_filename=file_name,
        #        mimetype='application/zip'
        #    )
        return send_file(zip_file_name, mimetype='application/zip', attachment_filename=file_name, as_attachment=True)
