from kfp import dsl
from kfp import compiler

@dsl.component
def rcb_task():
    print("Hello from RCB , we are here")

@dsl.pipeline(name="rcb-pipeline")
def rcb_pipeline():
    rcb_task()

if __name__ == "__main__":
    compiler.Compiler().compile(rcb_pipeline, "rcb_pipeline.yaml")