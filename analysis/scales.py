import subprocess
from pathlib import Path

from surround_brightness import data_management

ANALYSIS_FILE = Path(__file__).parent / "analysis-mlcm.Rmd"


def estimate_scales(participant, stimulus):
    """Estimate perceptual scale for given participant and stimulus

    Renders the RMarkdown-file `analysis-mclm.Rmd`
    with the provided participant and stimulus names as parameter values.
    The rendered `.pdf` version will be output to the participant's "analyzed" data directory,
    as will the `.csv`-files that the scale estimation produces.

    Parameters
    ----------
    participant : string
        initials/ID of participant
    stimulus : string
        full stimulus name
    """
    output_filename = f"{participant}_{stimulus}.analysis.pdf"
    output_filepath = data_management.results_dir / participant / "analyzed" / output_filename

    call = f"""rmarkdown::render('{ANALYSIS_FILE}',
                params=list(
                    participant='{participant}',
                    stimulus='{stimulus}'
                ),
                output_file='{output_filepath}'
            )"""

    subprocess.call(["Rscript", "--vanilla", "-e", call])


if __name__ == "__main__":
    participant = "DEMO"
    stimulus = "whites"

    estimate_scales(participant, stimulus)
