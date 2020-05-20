#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from flask_restplus import Resource, fields, Model, abort

from aops.applications.database.apis.repository.repository import Repostiory
from aops.applications.exceptions.exception import ResourceNotFoundError

from aops.applications.handlers.v1.repository import ns

repository_statistic_model = Model('RepositoryStatistic', {
    'repository_type': fields.String(required=True, description="The repository type's name"),
    'count': fields.Integer(required=True, description="The project number of the repository_type")
})

ns.add_model(repository_statistic_model.name, repository_statistic_model)


@ns.route('<int:identifier>/statistics/<string:repository_type>')
class RepositoryStatistic(Resource):
    """Celery Workers' statistics info."""

    @ns.doc('Get all workers and there detail information from SCHEDULER')
    @ns.param('identifier', 'business_group')
    @ns.marshal_list_with(repository_statistic_model)
    def get(self, identifier, repository_type):
        """Get all workers' statistics info."""
        try:
            workers = Repostiory().get_repository_count(identifier, repository_type)
        except ResourceNotFoundError as e:
            app.logger.error(e.message)
            abort(404, e.message)
        app.logger.info("Get all repository info with: {}".format(workers))
        return workers
