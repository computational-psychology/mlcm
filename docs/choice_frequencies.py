# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     custom_cell_magics: kql
#     notebook_metadata_filter: "jupytext,-kernelspec\x13"
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.2
# ---

# %% [markdown]
# # (Conjoint) choice frequencies

# %%
import pandas as pd

from mlcm import frequencies, utils

# %% [markdown]
# ## Example data

# %%
trial_data = pd.read_csv("trials_MLCM_SF_contrast.csv")
trial_data

# %% [markdown]
# On each trial of this example data,
# the participant judged a pair of stimuli
# -- `left` and `right`.

# %%
pair_names = ("left", "right")

# %% [markdown]
# The two stimuli are Gabor patches.
# They can physically differ along two dimensions:
# - `spatial freq`uency
# - `contrast`

# %%
dim_names = ("spatial_freq", "contrast")

# %% [markdown]
# Both of these physical dimensions were sampled at various values,
# i.e., _levels_.
# We can extract from the data, which (unique) stimulus levels were used:

# %%
stim_levels = utils.extract_stim_levels(
    trials=trial_data, dim_names=dim_names, pair_names=pair_names
)
stim_levels

# %% [markdown]
# Which means that all the unique stimuli are

# %%
utils.dimension_combinations(stim_levels)

# %% [markdown]
# All possible pairwise combinations of these unique stimuli were presented,
# except for pairs of physically identical (contrast _and_ spatial frequency) stimuli.
# Each pairwise combination (trial) was also repeated 10 times.

# %%
nrepeats = 10

# %% [markdown]
# ## Response choice frequency

# %% [markdown]
# The participant's `response` is which of the two stimuli (`left`, or `right`)
# had higher _perceived_ contrast (the _perceptual_ dimension).

# %% [markdown]
# For instance, in this trial, the participant chose the left stimulus
# as having higher perceived contrast.
# Both stimulus have the same spatial frequency,
# but the left (chosen) target has higher physical contrast

# %%
trial_data.loc[5]

# %% [markdown]
# We can also look at the trials where both targets have the same physical contrast,
# and narrow this down to some particular contrast value:

# %%
trial_data.query("contrast_left == contrast_right == 0.092")

# %% [markdown]
# We can see that the participant is in general quite consistent:
# for the exact same trial (same spatial frequency left and right),
# the response is usually the same:

# %%
trial_data.query(
    "contrast_left == contrast_right == 0.092 \
                  and spatial_freq_left == 0.5 \
                  and spatial_freq_right == 16.0"
)

# %% [markdown]
# If we add up all the times that the participant chose a particular stimulus,
# we get the _choice frequency_: the amount
# the amount of times the participant chose one stimulus over the other.
#
# $$ F(L | L, R) $$
#
# In this case, the choice frequency for choosing `"left"` was `5`,
# (and thus the complementary frequency of choosing `"right"` was `0`)
#
# $$\begin{align}
# F(L | L, R) &= 5 \\
# F(R | L, R) &= 5 - F(L | L, R) = 0
# \end{align}$$
#
#
# Specifically, this is a _conjoint_ choice frequency:
# since we are looking at a specific _unique stimulus combination_.

# %% [markdown]
# ### Pivot table
# Rather than going through each conjoint combination separately,
# we can construct a pivot table of these conjoint choice frequencies.
#
# To do this, we have to decided which choice to count frequency for,
# e.g., `"left"`

# %%
freqs_left = frequencies.response_choice(
    trials=trial_data, choice="left", dim_names=dim_names, pair_names=pair_names
)
freqs_left

# %% [markdown]
# Here, each cell contains a conjoint choice frequency.
# Each row defines the `"left"` stimulus (its `spatial_freq`uency and `contrast`),
# and each column defines the `"right"` stimulus similarly.
#
# Any paired combination that was never shown, gets choice frequency `NaN`.

# %% [markdown]
# We can focus on a specific spatial frequency, e.g., `0.5` cpd,
# and see that here the left target (defined on the rows)
# was chosen consistently when it has a higher physical contrast than the right target:

# %%
freqs_left.iloc[
    freqs_left.index.get_level_values("spatial_freq") == 0.5,
    freqs_left.columns.get_level_values("spatial_freq") == 0.5,
]

# %% [markdown]
# When we look at a different spatial frequency, `16.0` cpd,
# we see that the participant was less consistent:
# in some cases, the `"left"` target was chosen as higher perceived contrast.
# even it had a physically lower contrast.

# %%
freqs_left.iloc[
    freqs_left.index.get_level_values("spatial_freq") == 16,
    freqs_left.columns.get_level_values("spatial_freq") == 16,
]

# %% [markdown]
# We can also look at the complementary frequencies,
# where the participant chose the `"right"` stimulus:

# %%
freqs_right = frequencies.response_choice(
    trials=trial_data, choice="right", dim_names=dim_names, pair_names=pair_names
)

# %%
freqs_right.iloc[
    freqs_right.index.get_level_values("spatial_freq") == 16,
    freqs_right.columns.get_level_values("spatial_freq") == 16,
]

# %% [markdown]
# Here we see a similar pattern:
# the right target (defined by the columns) was chosen mostly
# when it had the higher physical contrast than the left target (rows),
# but not always (e.g. `{"right": 0.005, "left": 0.013} = 2`)

# %% [markdown]
# ## Collapse across choices

# %% [markdown]
# In most cases, we assume that the stimulus ordering within a paired combination does not matter,
# that is,
# the choice frequency of choosing stimulus $A$ over $B$ $P(A|A,B)$
# shouldn't depend on whether the pair is $(A, B)$ or $(B, A)$.
#
# Under this assumption, we can simply add up the two respective choice frequencies,
# for the two orderings of the pair:
# $$
# F(A | A,B) = F(L | L = A, R = B) + F(R | L = B, R = A)
# $$

# %% [markdown]
# In our pivot table(s),
# this is equivalent to adding one table of choice frequencies,
# to the _transpose_ of the other:

# %%
freqs = freqs_left.T + freqs_right

# %%
freqs.iloc[
    freqs_right.index.get_level_values("spatial_freq") == 16,
    freqs_right.columns.get_level_values("spatial_freq") == 16,
]

# %% [markdown]
# Here each cells shows the frequency of choosing the stimulus defined by the columnns.
# regardless of the ordering of the stimuli within a pair.
#
# What we can also see, is that if we add up cells mirrored over the major diagonal,
# we get the number of repeats, e.g., $3+7=10$ repeats.
# Thus, this representation is over-complete:
# we have all the information in just the upper triangle over the table;
# the lower triangle is equal to $N-F$.
#
# Therefore, we usually just keep the upper triangle (and set the lower to `NaN`):

# %%
freqs = frequencies.collapse(freqs_row=freqs_left, freqs_col=freqs_right)
freqs

# %% [markdown]
# ## All-in-one

# %%
frequencies.conjoint_choice(trials=trial_data, dim_names=dim_names, pair_names=pair_names)

# %% [markdown]
# ## Choice proportions / probabilities

# %% [markdown]
# If we consider the number of repeats per cell,
# we can also rescale these frequencies into choice proportions,
# or choice probabilities:

# %%
probs = freqs / nrepeats
probs
