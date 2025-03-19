// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

import "./AcademicToken.sol";

/**
 * @title DocumentNFT
 * @dev ERC721 token representing academic documents with immutability
 */
contract DocumentNFT is ERC721URIStorage, Ownable {
    struct Document {
        string fileHash;
        address uploader;
        uint256 timestamp;
        string metadata;
        bool isAssignment;
        uint256 deadline; // 0 if not applicable
    }

    // Document storage
    Document[] public documents;
    mapping(string => bool) private hashExists;
    mapping(uint256 => uint256) private gradeRecords; // tokenId => grade hash

    // Academic token contract
    AcademicToken private academicToken;

    // Constants
    uint256 private constant ON_TIME_REWARD = 10 * 10**18; // 10 tokens

    // Events
    event DocumentMinted(uint256 indexed tokenId, string fileHash, address uploader, string metadata);
    event GradeRecorded(uint256 indexed tokenId, uint256 gradeHash);

    constructor(address _tokenAddress) ERC721("Academic Document", "ADOC") Ownable(msg.sender) {
        academicToken = AcademicToken(_tokenAddress);
    }

    /**
     * @dev Create a new document NFT
     * @param fileHash Hash of the uploaded file
     * @param metadata Additional information about the document
     * @param isAssignment Whether this is an assignment submission
     * @param deadline Deadline timestamp (0 if not an assignment)
     * @return tokenId of the new NFT
     */
    function mintDocument(
        string memory fileHash,
        string memory metadata,
        bool isAssignment,
        uint256 deadline
    ) public returns (uint256) {
        require(!hashExists[fileHash], "Document already exists");

        uint256 tokenId = documents.length;
        documents.push(Document({
            fileHash: fileHash,
            uploader: msg.sender,
            timestamp: block.timestamp,
            metadata: metadata,
            isAssignment: isAssignment,
            deadline: deadline
        }));

        hashExists[fileHash] = true;
        _mint(msg.sender, tokenId);

        // If this is an assignment submission before deadline, reward the student
        if (isAssignment && deadline != 0 && block.timestamp <= deadline) {
            academicToken.awardTokens(
                msg.sender,
                ON_TIME_REWARD,
                "On-time assignment submission"
            );
        }

        emit DocumentMinted(tokenId, fileHash, msg.sender, metadata);
        return tokenId;
    }

    /**
     * @dev Record grade for an assignment
     * @param tokenId ID of the document NFT
     * @param gradeHash Hash of the grade information
     */
    function recordGrade(uint256 tokenId, uint256 gradeHash) public onlyOwner {
        require(_exists(tokenId), "Document does not exist");
        require(documents[tokenId].isAssignment, "Not an assignment");

        gradeRecords[tokenId] = gradeHash;
        emit GradeRecorded(tokenId, gradeHash);
    }

    /**
     * @dev Verify if a document exists with the given hash
     * @param fileHash Hash to verify
     * @return bool whether the document exists
     */
    function verifyDocument(string memory fileHash) public view returns (bool) {
        return hashExists[fileHash];
    }

    /**
     * @dev Get document count
     * @return uint256 count of documents
     */
    function getDocumentCount() public view returns (uint256) {
        return documents.length;
    }

    /**
     * @dev Get document details
     * @param tokenId Token ID of the document
     * @return Document struct with document details
     */
    function getDocument(uint256 tokenId) public view returns (
        string memory fileHash,
        address uploader,
        uint256 timestamp,
        string memory metadata,
        bool isAssignment,
        uint256 deadline
    ) {
        require(_exists(tokenId), "Document does not exist");
        Document memory doc = documents[tokenId];
        return (
            doc.fileHash,
            doc.uploader,
            doc.timestamp,
            doc.metadata,
            doc.isAssignment,
            doc.deadline
        );
    }

    /**
     * @dev Check if a document was submitted before deadline
     * @param tokenId Document token ID
     * @return bool whether submission was on time
     */
    function isSubmittedOnTime(uint256 tokenId) public view returns (bool) {
        require(_exists(tokenId), "Document does not exist");
        Document memory doc = documents[tokenId];

        if (!doc.isAssignment || doc.deadline == 0) {
            return false;
        }

        return doc.timestamp <= doc.deadline;
    }

    /**
     * @dev Get grade for a document
     * @param tokenId Document token ID
     * @return uint256 grade hash
     */
    function getGrade(uint256 tokenId) public view returns (uint256) {
        require(_exists(tokenId), "Document does not exist");
        return gradeRecords[tokenId];
    }
}