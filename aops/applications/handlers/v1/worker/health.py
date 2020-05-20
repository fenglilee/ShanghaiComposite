#!/usr/bin/env python
# -*- coding:utf-8 -*-
from flask import current_app as app
from flask_restplus import Resource, fields, Model, abort

from aops.applications.common.scheduler_request import SchedulerApi
from aops.applications.exceptions.exception import SchedulerError
from aops.applications.handlers.v1.worker import ns

worker_health_model = Model('WorkerHealth', {
    'cluster_name': fields.String(required=True, description="The worker's business cluster name"),
    'workers_number': fields.Integer(required=True, description="The healthy worker number of the cluster"),
    'workers_name_list': fields.List(
        fields.String(required=True, description="The healthy worker name of the cluster")),
})

ns.add_model(worker_health_model.name, worker_health_model)


@ns.route('/health')
class WorkersHealth(Resource):
    """Celery Workers details info."""

    @ns.doc('Get all workers and there detail information')
    @ns.marshal_list_with(worker_health_model)
    def get(self):
        """Get all todo items."""
        try:
            health_status = SchedulerApi("/v1/workers/health").get()
        except SchedulerError as e:
            app.logger.error(e.message)
            abort(502, e.message)
        app.logger.info("Get all workers' health status with: {}".format(health_status))
        return health_status
