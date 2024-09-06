***

## Table of Contents
* [Introduction](#introduction)
* [Available donation platforms](#available-donation-platforms)
  * [Opire](#opire)
    * [About Opire](#about-opire)
    * [How to use Opire](#how-to-use-opire)
      * [Create a reward](#create-a-reward)
      * [Pay a reward](#pay-a-reward)

***

## Introduction

AutoKey doesn't have its own platform for accepting donations, but the AutoKey community has shown an interest in having access to one and is currently trying out the [Opire](https://opire.dev/) platform to put bounties on AutoKey issues. This platform seems to be especially suitable for the AutoKey project because it allows community members to specify the type of development they'd like to see.

## Available donation platforms

### Opire

#### About Opire
[Opire](https://opire.dev/) is a reward platform that provides a convenient way for community members to incentivize development on specific issues in open-source programs by offering financial rewards that are handled directly between the community members and the developers.

A reward is a bounty that anyone create for any issue, with the minimum amount for any reward being $20. Anyone can also add to an existing reward to increase it. Anyone can claim a reward if they earn it by solving an issue and submitting a pull request that's accepted.

No money changes hands until or unless a pull request is accepted as the solution to a reward issue. At that point, the developer who solved the issue can use Opire to claim the reward and the person or persons who offered the reward receive a notification letting them know that the issue has been solved and payment is due.

Payment of rewards is on the honor system. If a person repeatedly creates awards and fails to pay for them when the issues have been solved, that person will no longer be able to create new rewards until the existing ones are paid in full.

Full documentation is available [here](https://docs.opire.dev).

#### How to use Opire

AutoKey has not yet installed the [Opire bot](https://docs.opire.dev/overview/install-bot) that offers commands that can be used in any [AutoKey issue](https://github.com/autokey/autokey/issues) or [AutoKey pull request](https://github.com/autokey/autokey/pulls) to create or manage rewards without having to log in to the Opire website. For now, community members can create or pay rewards on the Opire website.

##### Create a reward

1. Log in to the [Opire website](https://app.opire.dev/) using your GitHub account.
2. Click ***My dashboard*** in the left pane.
3. Click **Rewards** in the left pane.
4. Click the **Create a new reward** button in the right pane to create a new reward, providing the URL of the GitHub issue and the amount of the reward.

##### Pay a reward

When a person who offered a reward gets a notification that the issue has been solved:

1. Verify that the pull request satisfies the reward.
2. Use the dashboard on the [Opire website](https://app.opire.dev/) to pay the full reward amount to the developer directly via [Stripe](https://stripe.com/payments/payment-methods). Note that an additional 4% fee will be added on and given to Opire for handling the transaction.
