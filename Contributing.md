***

## Table of Contents
* [Introduction](#introduction)
* [Contributing code](#contributing-code)
* [Donations](#donations)
  * [Available donation platforms](#available-donation-platforms)
    * [Opire](#opire)
      * [About Opire](#about-opire)
      * [How to use Opire](#how-to-use-opire)
        * [Create a reward](#create-a-reward)
        * [Pay a reward](#pay-a-reward)

***

## Introduction
This project welcomes all sorts of help. Below are a few suggestions to get started:

* Adding to or editing the [documentation](https://github.com/autokey/autokey/wiki/Documentation).
* Adding to or editing the [wiki](https://github.com/autokey/autokey/wiki) with documentation, example scripts, workflow ideas, and other content.
* Answering questions and contributing to discussions in places like [Google Groups](https://github.com/autokey/autokey/wiki/Google-Groups), [Reddit](https://github.com/autokey/autokey/wiki/Reddit), and [Stack Exchange](https://github.com/autokey/autokey/wiki/StackExchange) that let other users and developers know we exist.
* [Contributing code](https://github.com/autokey/autokey/blob/develop/CONTRIBUTORS.rst) by adding new features, updating existing code, or fixing [issues](https://github.com/autokey/autokey/issues).
* Finding anything you feel you can change in the AutoKey project and making the change yourself.
* Providing user [community](https://github.com/autokey/autokey/wiki/Community) support, feedback, and general participation.
* Sharing your expertise with CI, CD, git, GitHub, Python, etc., in our [community](https://github.com/autokey/autokey/wiki/Community).
* Signing up with CodeTriage to receive a daily email with a link to an open AutoKey issue that needs help: [![Open Source Helpers](https://www.codetriage.com/autokey/autokey/badges/users.svg)](https://www.codetriage.com/autokey/autokey).
* Submitting [feature requests and/or bug reports](https://github.com/autokey/autokey/issues).
* Testing and recreating [issues](https://github.com/autokey/autokey/issues) in various [distributions](https://github.com/autokey/autokey/wiki/Current-Linux-distributions-shipping-AutoKey).
* Testing [changes](https://github.com/autokey/autokey/pulls), [new features](https://github.com/autokey/autokey/blob/develop/new_features.rst), [betas](https://github.com/autokey/autokey/releases?q=beta&expanded=true), and [new releases](https://github.com/autokey/autokey/releases).
* Writing articles about AutoKey.

Before embarking on any major effort, it's a good idea to discuss what you'd like to do on the [Gitter](https://gitter.im/autokey/autokey) platform to make sure it has a good chance of being accepted and to draw on our experience as to the best way to proceed.

## Contributing code

Autokey is currently undergoing large changes on its `develop` branch. If you are writing code for anything other than small bugfixes, you should base off that branch. It is very far ahead of `master`, and has tidier code.

`develop` is the only branch with a working test framework, which you should do your best to use for code you contribute. Currently test coverage is very low, but that should not be an excuse for making it worse---please include tests for your code. Feel free to ask for help with writing tests in your PR comments.

Finally, please read [CONTRIBUTERS.rst](https://github.com/autokey/autokey/blob/develop/CONTRIBUTORS.rst) on that same branch.

--- BlueDrink9, 2020-10-06

## Donations

AutoKey doesn't have its own platform for accepting donations, but the AutoKey community has shown an interest in having access to one and is currently trying out the [Opire](https://opire.dev/) platform to put bounties on AutoKey issues. This platform seems to be especially suitable for the AutoKey project because it allows community members to specify the type of development they'd like to see.

### Available donation platforms

#### Opire

##### About Opire
[Opire](https://opire.dev/) is a reward platform that provides a convenient way for community members to incentivize development on specific issues in open-source programs by offering financial rewards that are handled directly between the community members and the developers.

A reward is a bounty that anyone can create for any issue, with the minimum amount for a reward being $20. Anyone can also add to an existing reward to increase it and anyone can claim a reward if they earn it by solving an issue and submitting an accepted pull request.

A claim is a request for payment based on the completion of the specified task that has one or more rewards associated with it. A developer who solves an issue can use Opire to file a claim for the reward. The claim automatically triggers a notification to be sent to each creator of any rewards associated with that task letting them know that the issue has been solved and payment is due. It's then up to the reward creators to review the claim, examine the pull request, and decide whether or not to accept it as completion of the task and the solution to the reward issue. If the pull request is accepted, payment is made to the claimant by the reward creator(s).

Payment of rewards is done on the honor system. If a person repeatedly creates awards and fails to pay for them when the issues have been solved, that person will no longer be able to create new rewards until the existing ones are paid in full.

Full documentation is available [here](https://docs.opire.dev) and a video showing how it works is available [here](https://www.youtube.com/watch?v=pq7fluN44hA).

##### How to use Opire

AutoKey has not yet installed the [Opire bot](https://docs.opire.dev/overview/install-bot) that offers commands to use in any [AutoKey issue](https://github.com/autokey/autokey/issues) or [AutoKey pull request](https://github.com/autokey/autokey/pulls) to create or manage rewards without having to log in to the Opire website. For now, community members can create or pay rewards on the Opire website.

###### Create a reward

1. Log in to the [Opire website](https://app.opire.dev/) using your GitHub account.
2. Click **My dashboard** in the left pane.
3. Click **Rewards** in the left pane.
4. Click the **Create a new reward** button in the right pane to create a new reward, providing the URL of the GitHub issue and the amount of the reward.

###### Pay a reward

When a person who offered a reward gets a notification that the issue has been solved:

1. Verify that the pull request satisfies the reward. Below are some things to consider when doing this:
   * Check whether or not the name of the pull request's author matches that of the claimant.
   * Check whether or not the pull request has been merged.
   * Test out the code for that pull request to see if the issue has been solved by [cloning the pull request](https://github.com/autokey/autokey/wiki/GitHub-Cheat-Sheet#local---clone-a-pull-request) and [running the clone](https://github.com/autokey/autokey/wiki/GitHub-Cheat-Sheet#local---run-a-clone).
   * Consider whether you, the donor, are satisfied with the resolution of the issue.  If you have concerns, document them in the issue's comments section.
2. Use the dashboard on the [Opire website](https://app.opire.dev/) to pay the full reward amount to the developer directly via [Stripe](https://stripe.com/payments/payment-methods). Note that the total cost will consist of the reward amount plus the Stripe fee ($0.85 + 5.25%) and the Opire fee (4% of the reward) for handling the transaction.
