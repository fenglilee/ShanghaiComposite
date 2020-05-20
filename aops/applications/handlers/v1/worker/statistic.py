#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from flask_restplus import Resource, fields, Model, abort

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.exceptions.exception import SchedulerError

from aops.applications.handlers.v1.worker import ns

worker_model = Model('WorkerWithoutId', {
    'name': fields.String(required=True, description="The celery worker's name"),
    'active': fields.Integer(required=True, description="The active state task number of the worker"),
    'reserved': fields.Integer(required=True, description="The reserved state task number of the worker"),
    'scheduled': fields.Integer(required=True, description="The scheduled state task number of the worker"),
    'finished': fields.Integer(required=True, description="The tasks' total number of the worker"),
    'memory_usage': fields.String(required=True, description="The worker's memory usage of the worker"),
})

ns.add_model(worker_model.name, worker_model)


@ns.route('/statistic')
class Statistic(Resource):
    """Celery Workers' statistics info."""

    @ns.doc('Get all workers and there detail information from SCHEDULER')
    @ns.response(502, 'Scheduler server occurred error')
    @ns.marshal_list_with(worker_model)
    def get(self):
        """Get all workers' statistics info."""
        try:
            workers = SchedulerApi("/v1/workers/statistic").get()
        except SchedulerError as e:
            app.logger.error(e.message)
            abort(502, e.message)
        app.logger.info("Get all workers info with: {}".format(workers))
        return workers
