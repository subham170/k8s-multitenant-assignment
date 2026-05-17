from kfp import dsl
from kfp import compiler

@dsl.component
def rr_task():
    print("Hello from RR to qwerty")

@dsl.pipeline(name="rr-pipeline")
def rr_pipeline():
    rr_task()

if __name__ == "__main__":
    compiler.Compiler().compile(rr_pipeline, "pipelines/rr_pipeline.yaml")