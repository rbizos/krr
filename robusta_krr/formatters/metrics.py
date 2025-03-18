import re

from prometheus_client import Gauge

from robusta_krr.api import formatters
from robusta_krr.core.models.allocations import ResourceType
from robusta_krr.core.models.result import Result
from robusta_krr.core.models.severity import Severity

label_names = ["namespace", "name", "kind", "cluster", "resource"]

namespace_labels = ["cluster", "dc", "env", "namespace"]
identity_labels = ["kind", "name", "container"]

controller_resource_request_score = Gauge(
    name="krr_controller_resource_request_score",
    documentation="Controller Score in term of resources",
    labelnames=[*namespace_labels, *identity_labels, "resource"],
)

controller_score = Gauge(
    name="krr_controller_overall_score",
    documentation="Controller Score in term of resources",
    labelnames=[*namespace_labels, *identity_labels],
)


controller_instance_count = Gauge(
    name="krr_controller_instance_count",
    documentation="Controller Score in term of resources",
    labelnames=[*namespace_labels, *identity_labels],
)

controller_resource_request_current = Gauge(
    name="krr_controller_resource_request_current",
    documentation="Controller Score in term of resources",
    labelnames=[*namespace_labels, *identity_labels, "resource"],
)

controller_resource_request_recommended = Gauge(
    name="krr_controller_resource_request_recommended",
    documentation="Controller Score in term of resources",
    labelnames=[*namespace_labels, *identity_labels, "resource"],
)

cpu_price = Gauge(
    name="krr_cpu_price",
    documentation="Controller Score in term of resources",
    labelnames=["dc"],
)

cpu_price.labels("dc1").set(0.056088)


cpu_emission = Gauge(
    name="krr_cpu_idle_yearly_emission",
    documentation="Controller Score in term of resources",
    labelnames=["dc"],
)

cpu_emission.labels("dc1").set(56*14)


# cluster to cluster, dc env <cluster>-<dc>.<env>
# with a regex
pattern = re.compile(r"^([^-]+)-([^.]+)\.(.+)$")


def expand_cluster_name(cluster: str) -> tuple[str, str, str]:
    match = pattern.match(cluster)
    cluster, dc, env = match.groups()
    return cluster, dc, env


def severity_to_int(severity: Severity):
    match severity:
        case Severity.CRITICAL:
            return 0
        case Severity.WARNING:
            return 1
        case Severity.OK:
            return 2
        case Severity.GOOD:
            return 3
        case _:
            return -1


@formatters.register()
def metrics(result: Result) -> str:
    for scan in result.scans:

        controller_instance_count.labels(
            *expand_cluster_name(scan.object.cluster),
            scan.object.namespace,
            scan.object.kind,
            scan.object.name,
            scan.object.container,
        ).set(len([ pod for pod in scan.object.pods if not pod.deleted]))


        # Set the overall score

        controller_score.labels(
            *expand_cluster_name(scan.object.cluster),
            scan.object.namespace,
            scan.object.kind,
            scan.object.name,
            scan.object.container,
        ).set(severity_to_int(scan.severity))

        # Set the resource score
        for resource in [ResourceType.CPU, ResourceType.Memory]:
            controller_resource_request_score.labels(
                *expand_cluster_name(scan.object.cluster),
                scan.object.namespace,
                scan.object.kind,
                scan.object.name,
                scan.object.container,
                resource.name,
            ).set(severity_to_int(scan.recommended.requests[resource].severity))

            allocated_value = scan.object.allocations.requests[resource]
            if not isinstance(allocated_value, float):
                allocated_value = -1

            controller_resource_request_current.labels(
                *expand_cluster_name(scan.object.cluster),
                scan.object.namespace,
                scan.object.kind,
                scan.object.name,
                scan.object.container,
                resource.name,
            ).set(allocated_value)

            recommended_value = scan.recommended.requests[resource].value
            if not isinstance(recommended_value, float):
                recommended_value = -1

            controller_resource_request_recommended.labels(
                *expand_cluster_name(scan.object.cluster),
                scan.object.namespace,
                scan.object.kind,
                scan.object.name,
                scan.object.container,
                resource.name,
            ).set(recommended_value)





        print(scan.object, scan.severity)
    return "updated metrics"
