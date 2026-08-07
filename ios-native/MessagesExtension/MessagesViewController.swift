//  MessagesViewController.swift
//  HumxnMed — iMessage extension (care coordination)
//
//  A small, native iMessage app that helps a patient loop family or a caregiver into
//  their health: tap a card and it inserts a branded HumxnMed message with a link back
//  into the app. Intentionally simple and PHI-free — it composes conversation starters
//  and an invite, never the person's health records (those stay on-device in the app).
//
//  Code-only (no storyboard): the extension's Info.plist points NSExtensionPrincipalClass
//  straight at this class.

import UIKit
import Messages

final class MessagesViewController: MSMessagesAppViewController {

    // Forest + gold, matched to the app.
    private let forest = UIColor(red: 0x03/255.0, green: 0x47/255.0, blue: 0x30/255.0, alpha: 1)
    private let gold   = UIColor(red: 0xC9/255.0, green: 0xA2/255.0, blue: 0x27/255.0, alpha: 1)
    private let appURL = URL(string: "https://humxnmed.millennialscreatives.com/?ref=imessage")!

    // The cards a user can send. caption/subcaption ride on the iMessage bubble.
    private struct Card { let title: String; let subtitle: String; let caption: String; let subcaption: String }
    private let cards: [Card] = [
        Card(title: "Talk about a health concern",
             subtitle: "Open the conversation gently",
             caption: "Can we talk about a health concern?",
             subcaption: "Shared with HumxnMed"),
        Card(title: "Come to my appointment",
             subtitle: "Ask someone to join you",
             caption: "Could you come to my doctor's appointment with me?",
             subcaption: "Shared with HumxnMed"),
        Card(title: "Help me understand this",
             subtitle: "Loop in a caregiver",
             caption: "I got some health news I want help understanding.",
             subcaption: "Shared with HumxnMed"),
        Card(title: "Invite to HumxnMed",
             subtitle: "Understand health in plain language",
             caption: "I use HumxnMed to understand my health in plain language — join me.",
             subcaption: "humxnmed.millennialscreatives.com")
    ]

    private let stack = UIStackView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        buildUI()
    }

    private func buildUI() {
        let title = UILabel()
        title.text = "Share with someone who cares"
        title.font = .systemFont(ofSize: 15, weight: .semibold)
        title.textColor = .label
        title.numberOfLines = 0

        stack.axis = .vertical
        stack.spacing = 10
        stack.translatesAutoresizingMaskIntoConstraints = false

        stack.addArrangedSubview(title)
        for (i, card) in cards.enumerated() {
            stack.addArrangedSubview(makeButton(card, tag: i))
        }

        let scroll = UIScrollView()
        scroll.translatesAutoresizingMaskIntoConstraints = false
        scroll.addSubview(stack)
        view.addSubview(scroll)

        NSLayoutConstraint.activate([
            scroll.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 16),
            scroll.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -16),
            scroll.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 12),
            scroll.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -12),

            stack.leadingAnchor.constraint(equalTo: scroll.contentLayoutGuide.leadingAnchor),
            stack.trailingAnchor.constraint(equalTo: scroll.contentLayoutGuide.trailingAnchor),
            stack.topAnchor.constraint(equalTo: scroll.contentLayoutGuide.topAnchor),
            stack.bottomAnchor.constraint(equalTo: scroll.contentLayoutGuide.bottomAnchor),
            stack.widthAnchor.constraint(equalTo: scroll.frameLayoutGuide.widthAnchor)
        ])
    }

    private func makeButton(_ card: Card, tag: Int) -> UIControl {
        let container = UIControl()
        container.tag = tag
        container.backgroundColor = forest
        container.layer.cornerRadius = 14
        container.addTarget(self, action: #selector(cardTapped(_:)), for: .touchUpInside)
        container.translatesAutoresizingMaskIntoConstraints = false

        let t = UILabel()
        t.text = card.title
        t.font = .systemFont(ofSize: 16, weight: .bold)
        t.textColor = .white
        t.numberOfLines = 0

        let s = UILabel()
        s.text = card.subtitle
        s.font = .systemFont(ofSize: 13, weight: .regular)
        s.textColor = UIColor(white: 1, alpha: 0.75)
        s.numberOfLines = 0

        let v = UIStackView(arrangedSubviews: [t, s])
        v.axis = .vertical
        v.spacing = 2
        v.isUserInteractionEnabled = false
        v.translatesAutoresizingMaskIntoConstraints = false
        container.addSubview(v)

        NSLayoutConstraint.activate([
            v.leadingAnchor.constraint(equalTo: container.leadingAnchor, constant: 16),
            v.trailingAnchor.constraint(equalTo: container.trailingAnchor, constant: -16),
            v.topAnchor.constraint(equalTo: container.topAnchor, constant: 14),
            v.bottomAnchor.constraint(equalTo: container.bottomAnchor, constant: -14)
        ])
        return container
    }

    @objc private func cardTapped(_ sender: UIControl) {
        guard let conversation = activeConversation else { return }
        let card = cards[sender.tag]

        let layout = MSMessageTemplateLayout()
        layout.image = brandImage()
        layout.caption = card.caption
        layout.subcaption = card.subcaption

        let message = MSMessage()
        message.layout = layout
        message.url = appURL

        conversation.insert(message) { _ in }

        // Collapse back to compact after inserting.
        requestPresentationStyle(.compact)
    }

    // Draw the branded card image at composition time (no bundled asset to keep in sync).
    private func brandImage() -> UIImage {
        let size = CGSize(width: 900, height: 675) // 4:3, matches the iMessage layout image
        let renderer = UIGraphicsImageRenderer(size: size)
        return renderer.image { ctx in
            forest.setFill()
            ctx.fill(CGRect(origin: .zero, size: size))

            // gold "HM" wordmark
            let hm = "HM"
            let hmAttr: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 220, weight: .heavy),
                .foregroundColor: gold
            ]
            let hmSize = (hm as NSString).size(withAttributes: hmAttr)
            (hm as NSString).draw(at: CGPoint(x: (size.width - hmSize.width) / 2,
                                              y: size.height / 2 - hmSize.height + 40),
                                  withAttributes: hmAttr)

            let word = "HumxnMed"
            let wAttr: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 64, weight: .semibold),
                .foregroundColor: UIColor.white
            ]
            let wSize = (word as NSString).size(withAttributes: wAttr)
            (word as NSString).draw(at: CGPoint(x: (size.width - wSize.width) / 2,
                                                y: size.height / 2 + 70),
                                    withAttributes: wAttr)
        }
    }
}
