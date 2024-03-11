import subprocess

from image_builder.docker import Docker


def run_and_check_result(cmd):
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise Exception(result.stderr)


def publish_to_additional_repository(initial_repository, additional_repository, tags):
    for tag in tags:
        from_tag = f"{initial_repository}:{tag}"
        tag_cmd = ["docker", "pull", from_tag]
        print(f"Running command: {' '.join(tag_cmd)}")
        run_and_check_result(tag_cmd)

    Docker.login(additional_repository.split("/")[0])

    for tag in tags:
        from_tag = f"{initial_repository}:{tag}"
        to_tag = f"{additional_repository}:{tag}"
        tag_cmd = ["docker", "tag", from_tag, to_tag]
        print(f"Running command: {' '.join(tag_cmd)}")
        run_and_check_result(tag_cmd)
        push_cmd = ["docker", "push", to_tag]
        print(f"Running command: {' '.join(push_cmd)}")
        run_and_check_result(push_cmd)
